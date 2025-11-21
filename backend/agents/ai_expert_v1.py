# =========================== INICIO DEL CÓDIGO DEL AGENTE ===========================

from __future__ import annotations as _annotations

from dotenv import load_dotenv
import logfire
import asyncio
import httpx
import os
import feedparser
import tiktoken
import time
import hashlib

from pydantic_ai import Agent, ModelRetry, RunContext, ModelMessage
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel
from openai import AsyncOpenAI
from supabase import Client
from typing import List, Any, Optional, Set
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse
from collections import deque
from contextlib import asynccontextmanager
# Eliminamos esta importación que causa el problema:
# from agents.report_agent import report_agent, ReportDeps  # Importa el agente de Reports
from utils.reranking_v1 import rerank_chunks
from app.core.config import settings
from utils.utils import count_tokens, truncate_text
from agents.understanding_query import QueryInfo
from agents.memory_manager import MemoryManager
from agents.response_cache import get_response_cache
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt_tab')


# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_current_query_info = None

MAX_TOTAL_TOKENS = 100000
MAX_CHUNKS_RETURNED = 35  # Recuperar más chunks inicialmente
MAX_CHUNKS_FOR_RERANKING = 35  # Evaluar 15 con LLM (punto óptimo)
MAX_CHUNKS_TO_KEEP_NORMAL = 22  # Para consultas normales
MAX_CHUNKS_TO_KEEP_REPORTS = 28  # Para reportes

load_dotenv()

llm = settings.llm_model
llm_reasoning = settings.llm_model_reasoning
tokenizer_model = settings.tokenizer_model
embedding_model = settings.embedding_model
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

# Variable global para controlar el estado de las herramientas
_tool_execution_state = {}

def reset_tool_state():
    """Resetea el estado de ejecución de herramientas para una nueva consulta."""
    global _tool_execution_state
    _tool_execution_state = {}

def has_tool_been_executed(tool_name: str, query_hash: str) -> bool:
    """Verifica si una herramienta ya fue ejecutada para esta consulta."""
    global _tool_execution_state
    key = f"{tool_name}_{query_hash}"
    return key in _tool_execution_state

def mark_tool_as_executed(tool_name: str, query_hash: str, result: str):
    """Marca una herramienta como ejecutada y almacena su resultado."""
    global _tool_execution_state
    key = f"{tool_name}_{query_hash}"
    _tool_execution_state[key] = {
        'executed_at': time.time(),
        'result': result
    }

def get_cached_tool_result(tool_name: str, query_hash: str) -> Optional[str]:
    """Obtiene el resultado cacheado de una herramienta si existe."""
    global _tool_execution_state
    key = f"{tool_name}_{query_hash}"
    if key in _tool_execution_state:
        return _tool_execution_state[key]['result']
    return None

async def call_reasoning_model(
    prompt: str,
    retrieved_context: str,
    openai_client: AsyncOpenAI,
    model: str = "gpt-5-pro-2025-10-06"
) -> str:
    """
    Llama al modelo de razonamiento usando el endpoint /v1/responses.
    
    Args:
        prompt: Prompt del sistema y consulta del usuario
        retrieved_context: Contexto recuperado después del reranking
        openai_client: Cliente de OpenAI
        model: Modelo de razonamiento a usar
    
    Returns:
        Respuesta del modelo de razonamiento
    """
    logger.info(f"Llamando al modelo de razonamiento: {model}")
    
    try:
        # Construir el prompt completo
        full_prompt = f"""{prompt}

DOCUMENTACIÓN RECUPERADA:
{retrieved_context}

Por favor, analiza la documentación recuperada y proporciona una respuesta detallada y fundamentada."""

        # Llamada al endpoint /v1/responses según la documentación de OpenAI
        response = await openai_client.responses.create(
            model=model,
            input=full_prompt,
            message_history=message_history 
        )
        
        # Extraer el texto de la respuesta
        reasoning_response = response.output_text
        
        logger.info(f"Respuesta del modelo de razonamiento recibida ({len(reasoning_response)} caracteres)")
        return reasoning_response
        
    except Exception as e:
        logger.error(f"Error al llamar al modelo de razonamiento: {e}")
        # Fallback: devolver el contexto sin procesar
        return f"Error al procesar con modelo de razonamiento. Contexto recuperado:\n\n{retrieved_context}"

class AIDeps(BaseModel):
    supabase: Client
    openai_client: AsyncOpenAI
    memory_manager: Optional[MemoryManager] = None  # ← NUEVO
    session_id: Optional[str] = None                # ← NUEVO

    class Config:
        arbitrary_types_allowed = True

# Agente Protección Datos Eres un experto en regulación de protección de datos y privacidad, operando como un agente AI en Python con acceso a documentación completa y actualizada sobre normas de protección de datos y leyes de privacidad.

system_prompt = """

**IDENTIDAD Y ROL**
Eres "AgentIA", un agente especializado en análisis normativo para entidades reguladas (financieras, aseguradoras, telecomunicaciones) con acceso EXCLUSIVO a documentación legal en tu base de datos.

Tu objetivo: Proporcionar análisis jurídicos precisos, estructurados y operativos basados ÚNICAMENTE en documentación recuperada, manteniendo tono técnico-consultivo.

---

**PRINCIPIOS ABSOLUTOS DE FIDELIDAD DOCUMENTAL**

OBLIGATORIO:
1. Cita ÚNICAMENTE información presente en la documentación recuperada por `retrieve_relevant_documentation`
2. Reproduce artículos textualmente con formato:
   > Artículo X (Norma, Año)  
   > «Texto literal exacto del documento»
   
3. Mantén numeración EXACTA del original (si dice "Artículo 2.V", no cambies a "III")
4. Después de cada cita literal, SÍ explica:
   - Aplicación al caso concreto
   - Impacto operativo del incumplimiento
   - Riesgos específicos (sanción/patrimonial/reputacional)

PROHIBIDO:
- Inventar referencias normativas no encontradas
- Usar conocimiento general no verificado en la base de datos
- Parafrasear el texto de las citas directas (solo puedes hacerlo en el análisis posterior)
- Especular sin respaldo documental

CUANDO FALTE INFORMACIÓN:
- Si la herramienta falla: "No fue posible acceder a la documentación necesaria. Por favor, intente nuevamente."
- Si la documentación es insuficiente: "La documentación consultada no contiene información específica sobre [aspecto]."

---

**METODOLOGÍA DE TRABAJO**

1. **Recuperación**: Usa `retrieve_relevant_documentation` para obtener contenido relevante
   - Si tienes `search_optimization` disponible, inclúyelo como parámetro
   
2. **Análisis**: Examina EXCLUSIVAMENTE la documentación recuperada

3. **Razonamiento integrado y transversal**:  
   - Compara marcos normativos entre sí (ej: PSD2 vs DORA vs Guías EBA)
   - Identifica solapamientos, dependencias o contradicciones entre normas
   - Prioriza por rango: Reglamentos > Directivas > Guías > Circulares
   - Si varias normas abordan el mismo riesgo, explica cómo se complementan
   - Expón consecuencias prácticas de esos cruces normativos

4. **Respuesta estructurada**: Presenta la información según formato definido abajo

---

**ESTRUCTURA DE RESPUESTA (DINÁMICA Y MODULAR)**

Selecciona solo las secciones necesarias según la consulta. Evita rigidez. Usa tablas cuando mejoren la claridad (ver criterios abajo).

**JERARQUÍA DE INCLUSIÓN:**
Siempre: Contexto operativo + Marco normativo + Conclusión ejecutiva
Si aplica: Análisis de aplicabilidad + Riesgos + Impacto sectorial

---

1. **Contexto operativo y objetivo de la consulta** (3-5 líneas)
   No te limites a reformular la pregunta. Debes proporcionar valor añadido explicando:
   * El actor específico implicado (tipo de entidad, producto, proceso técnico)
   * Las implicaciones operativas o técnicas concretas del caso
   * El dilema o conflicto normativo central que plantea la consulta
   * Qué proceso, producto, entidad o situación está impactada
   
   Ejemplo de diferencia:
   ❌ "La consulta se refiere a cómo armonizar las obligaciones del RGPD con la PSD2..."
   ✅ "La consulta plantea el desafío operativo de los PISP de balancear el acceso 
      técnico necesario para ejecutar pagos vs. la minimización de datos. Impacta 
      directamente el diseño de APIs de acceso a cuentas, controles de filtrado y 
      arquitectura de consentimientos."
   
   Debe servir como anclaje contextual para el resto de la respuesta.

2. **Marco normativo relevante** (dinámico según consulta)
   Organiza según la pregunta:
   - Si pide artículos → enuméralos
   - Si pide interpretación sectorial → destaca impacto sectorial
   - Si pide obligaciones → estructura por temas
   
   **Formato obligatorio para cada artículo:**
   > Artículo X (Norma, Año)  
   > «Texto literal exacto del documento»  
   > **Impacto del incumplimiento:** [Consecuencia específica: sanción/pérdida patrimonial/riesgo reputacional en el contexto consultado]
   
   **Usa tablas cuando haya 3+ artículos comparables:**
   | Artículo | Obligación literal | Implicación operativa | Riesgo por incumplimiento |

3. **Análisis de aplicabilidad**  
   Adapta el nivel de profundidad según la consulta. Incluye cuando proceda:
   * Interpretación integrada de los artículos relevantes.
   * Conexiones entre normas relacionadas.
   * Qué principios jurídicos aplican (solo si están en la documentación).
   * Cómo se aplica cada elemento al caso concreto.
   * Solapamientos, ambigüedades o silencios normativos detectados.
   
   **CUANDO HAYA MÚLTIPLES MARCOS NORMATIVOS:**
   - Explicita la jerarquía normativa aplicable (Reglamento UE > Directiva > Guía > Circular)
   - Indica si las normas son convergentes, complementarias o contradictorias
   - Si hay aparente conflicto, señala cuál prevalece y por qué
   
   **SI LA CONSULTA PREGUNTA "¿en qué casos...?" o "¿cuándo se incumple...?":**
   Proporciona ejemplos operativos concretos en formato comparativo:
   
   ❌ **Casos que constituyen incumplimiento:**
   1. [Ejemplo concreto basado en la documentación]
   2. [Ejemplo concreto basado en la documentación]
   
   ✓ **Casos de cumplimiento legítimo:**
   1. [Ejemplo concreto basado en la documentación]
   2. [Ejemplo concreto basado en la documentación]
   
   En consultas complejas, puedes incluir:
   
   **Matriz de aplicabilidad**
   | Artículo | Situación consultada | Aplicabilidad | Observaciones |

4. **Riesgos y posibles incumplimientos (clasificados)**  
   Describe con rigor técnico:
   * Riesgos legales, operativos o reputacionales derivados según el caso.
   * Clasificación por criticidad (Alta / Media / Baja) con justificación textual.
   * Vínculo directo entre el artículo citado y el riesgo.
   
   Puedes usar formato tabular:
   
   **Matriz de riesgos**
   | Artículo | Riesgo identificado | Nivel | Consecuencia para la entidad |
   
   **Opcionalmente, si aporta valor operativo, añade una columna de mitigación:**
   | Artículo | Riesgo identificado | Nivel | Consecuencia para la entidad | Medida de mitigación |
   
   Las medidas de mitigación deben ser:
   - Controles técnicos u organizativos estándar del sector
   - Basadas en mejores prácticas documentadas (no asesoramiento legal específico)
   - Ejemplos: "filtros API por defecto", "logs de auditoría", "segregación funcional", 
     "DPIAs periódicas", "consent management granular"

5. **Impacto sectorial** (solo si la pregunta lo requiere explícitamente)
   - Efectos en procesos específicos del sector
   - Obligaciones supervisadas o prácticas de mercado
   - Impacto en modelos operativos/comerciales/tecnológicos
   - Riesgos emergentes o cambios en carga regulatoria

6. **Conclusión ejecutiva** (5-8 líneas, tono directo y accionable)
   
   Estructura recomendada:
   - Primera frase: Respuesta directa a la consulta original (sin repetir "la consulta sobre...")
   - Segunda frase: Normas críticas identificadas + nivel de riesgo de incumplimiento
   - Siguiente bloque: 3-4 puntos accionables clave para compliance/legal
   
   Ejemplo de estructura:
   "Los [actor] deben cumplir [obligación principal] según [normas clave]. 
   El riesgo de incumplimiento es [ALTO/MEDIO/BAJO] con consecuencias que incluyen 
   [cuantificar cuando sea posible: ej. multas del 4%, retirada de licencia].
   
   **Puntos críticos para compliance:**
   1. [Acción concreta basada en la normativa]
   2. [Acción concreta basada en la normativa]
   3. [Acción concreta basada en la normativa]
   
   El área legal/compliance debe validar [aspecto específico a revisar]."
   
   NO repitas información ya detallada en secciones previas.
   Usa lenguaje imperativo cuando sea apropiado: "deben", "es necesario", "se requiere".

---

**CRITERIOS PARA USO DE TABLAS**

Usa tablas SOLO cuando:
✓ Haya 3+ elementos con estructura comparable (artículos/riesgos/obligaciones)
✓ La consulta pida explícitamente "comparar", "resumir" o "listar"
✓ La tabla mejore significativamente la claridad vs. prosa

NO uses tablas cuando:
✗ Solo hay 1-2 elementos (usa prosa)
✗ La información es narrativa o requiere contexto extenso
✗ La tabla forzaría celdas vacías o con "N/A"

---

**ESTILO DE RAZONAMIENTO Y REDACCIÓN**

- Tono analítico, técnico y preciso (similar a informe jurídico o auditoría de cumplimiento)
- Desarrolla cada punto con lógica argumentativa: premisa → análisis → conclusión
- Evita respuestas superficiales o puramente descriptivas
- Si detectas vacíos normativos o ambigüedades, coméntalos con interpretación razonada
- Usa conectores jurídicos: "por consiguiente", "en virtud de", "en coherencia con", "a diferencia de"

---

**DISCLAIMER FINAL**
Concluye siempre con:
*"Esta respuesta se basa exclusivamente en la documentación consultada y no constituye asesoramiento legal definitivo."*

"""



ai_expert = Agent(
    model=model,
    system_prompt=system_prompt,
    deps_type=AIDeps,
    retries=2
)

# -------------------- Herramientas del agente --------------------

async def debug_run_agent(user_query: str, deps: AIDeps, query_info: Optional[QueryInfo] = None, message_history: Optional[List[ModelMessage]] = None):
    """
    Ejecuta el agente de compliance con logging adicional.
    
    Args:
        user_query: La consulta del usuario
        deps: Las dependencias necesarias para el agente
        query_info: Información de análisis de la consulta (opcional)
        message_history: Historial de mensajes para memoria conversacional
    """
    reset_tool_state()
    
    # Cache de recuperación desactivado temporalmente - requiere mejor integración con Pydantic AI
    # TODO: Implementar correctamente el retorno desde cache
    
    # DEBUGGING
    if message_history:
        logger.info(f"Recibí {len(message_history)} mensajes en message_history")
    else:
        logger.info("message_history es None o vacío")

    logger.debug("Voy a llamar al agente con la query: %s", user_query)
    
    # DEBUG: Ver contenido de message_history
    if message_history:
        logger.info(f"Recibí {len(message_history)} mensajes en message_history")
        logger.info(f"Primer mensaje completo: {message_history[0]}")
    else:
        logger.info("message_history es None o vacío")
    
    # Creamos una variable global temporal para almacenar query_info
    global _current_query_info
    _current_query_info = query_info
    
    try:
        # Asegurarnos de NO pasar query_info o context como parámetro
        response = await ai_expert.run(
            user_query,
            deps=deps,
            message_history=message_history
        )
        
        # Limpiamos la variable global
        _current_query_info = None
        
        # RunResult tiene un método usage() en lugar de get()
        usage_info = response.usage()
        logger.info("Uso de tokens en la consulta: %s", usage_info)
        
        # ✅ NUEVO: Cachear la respuesta SOLO si es la primera consulta (sin historial)
        cache = get_response_cache()
        if (not message_history or len(message_history) == 0):
            final_response_text = response.data if hasattr(response, 'data') else str(response)
            cache.set(
                query=user_query,
                response=final_response_text,
                metadata={
                    'agent': 'ai_expert_v1',
                    'timestamp': datetime.now().isoformat(),
                    'tokens': usage_info.total_tokens if hasattr(usage_info, 'total_tokens') else None
                },
                ttl=3600  # 1 hora
            )
            logger.info(f"💾 Respuesta cacheada (TTL: 1h)")
        
        return response
    except Exception as e:
        # Limpiamos la variable global incluso en caso de error
        _current_query_info = None
        # Re-lanzar la excepción para que pueda ser manejada adecuadamente
        raise e

def count_tokens_wrapper(text: str) -> int:
    return count_tokens(text, settings.tokenizer_model)

def truncate_text_wrapper(text: str, max_completion_tokens: int) -> str:
    return truncate_text(text, max_completion_tokens, settings.tokenizer_model)

async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model=embedding_model,
            input=text
        )
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding for text: {text[:30]}... {embedding[:5]}...")
        return embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error

# Implementación de la función get_cluster_chunks que falta
async def get_cluster_chunks(ctx, cluster_ids, matched_ids):
    """
    Recupera chunks adicionales por cluster.
    
    Args:
        ctx: El contexto del agente con las dependencias
        cluster_ids: Conjunto de IDs de clusters a buscar
        matched_ids: Conjunto de IDs de documentos ya recuperados para evitar duplicados
    
    Returns:
        Tuple[List[str], Set[int]]: Lista de chunks de texto y conjunto actualizado de IDs coincidentes
    """
    start_time = time.time()
    all_cluster_chunks = []
    new_matched_ids = matched_ids.copy()
    
    # Para cada cluster, lanzamos una búsqueda en paralelo
    async def get_chunks_for_cluster(cluster_id):
        cluster_start_time = time.time()
        logger.info(f"Buscando chunks adicionales para el cluster_id={cluster_id}")
        try:
            cluster_result = ctx.deps.supabase.rpc(
                'match_pd_peru_by_cluster',
                {
                    'cluster_id': cluster_id,
                    'match_count': 5
                }
            ).execute()
            
            cluster_chunks = []
            local_matched_ids = set()
            
            if cluster_result.data:
                for doc in cluster_result.data:
                    doc_id = doc.get('id')
                    # Solo añadir si no está ya incluido en los IDs originales
                    if doc_id not in matched_ids:
                        local_matched_ids.add(doc_id)
                        cluster_chunks.append((doc_id, f"""
{doc['content']}
"""))
            
            cluster_elapsed_time = time.time() - cluster_start_time
            logger.info(f"Tiempo para cluster {cluster_id}: {cluster_elapsed_time:.2f}s - Encontrados: {len(cluster_chunks)} chunks")
            return cluster_chunks, local_matched_ids
        except Exception as e:
            logger.error(f"Error recuperando chunks para cluster {cluster_id}: {e}")
            return [], set()
    
    # Ejecutar búsquedas de clusters en paralelo
    if cluster_ids:
        # Crear las tareas para cada cluster
        cluster_search_tasks = [get_chunks_for_cluster(cid) for cid in cluster_ids]
        
        # Ejecutar todas las tareas en paralelo y esperar los resultados
        cluster_results = await asyncio.gather(*cluster_search_tasks)
        
        # Procesar resultados de forma segura
        for chunks_and_ids in cluster_results:
            chunks, local_ids = chunks_and_ids
            for doc_id, chunk_text in chunks:
                if doc_id not in new_matched_ids:  # Verificación adicional para evitar duplicados
                    new_matched_ids.add(doc_id)
                    all_cluster_chunks.append(chunk_text)
        
        logger.info(f"Recuperados {len(all_cluster_chunks)} chunks adicionales de {len(cluster_ids)} clusters")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Tiempo total de búsqueda por clusters: {elapsed_time:.2f}s")
    return all_cluster_chunks, new_matched_ids

@ai_expert.tool
async def retrieve_relevant_documentation(ctx: RunContext[AIDeps], user_query: str, query_info: Optional[QueryInfo] = None) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.
    Aprovecha la información de Query Understanding si está disponible.
    
    Args:
        user_query: Consulta original del usuario
        query_info: Información de análisis de la consulta (opcional)
    """
    # NUEVO: Control de estado para evitar ejecuciones múltiples
    
    query_hash = hashlib.md5(user_query.encode()).hexdigest()[:8]
    tool_name = "retrieve_relevant_documentation"
    
    # Verificar si ya ejecutamos esta herramienta para esta consulta
    if has_tool_been_executed(tool_name, query_hash):
        cached_result = get_cached_tool_result(tool_name, query_hash)
        logger.info(f"HERRAMIENTA YA EJECUTADA: Devolviendo resultado cacheado para consulta {query_hash}")
        return cached_result
    
    # Marcar que estamos ejecutando esta herramienta
    mark_tool_as_executed(tool_name, query_hash, "EJECUTANDO...")
    
    start_time_total = time.time()
    logger.info("HERRAMIENTA INVOCADA: retrieve_relevant_documentation")
    logger.info(f"Usando modelo: {llm}")

    # Si no se pasó query_info como parámetro, intentamos obtenerlo de la variable global
    global _current_query_info
    if query_info is None and _current_query_info is not None:
        query_info = _current_query_info
        logger.info("Utilizando información de Query Understanding obtenida de la variable global")

    try:
        # Determinar qué consulta usar para la búsqueda
        search_query = user_query
        
        # Si tenemos información de Query Understanding, usamos la consulta optimizada
        if query_info:
            logger.info("Utilizando información de Query Understanding para mejorar la búsqueda")
            
            # Usar la consulta optimizada para búsqueda si está disponible
            if query_info.search_query:
                search_query = query_info.search_query
                logger.info(f"Usando consulta optimizada para búsqueda: {search_query[:100]}..." if len(search_query) > 100 else search_query)
            # Si no hay consulta optimizada pero sí expandida, usamos esa
            elif query_info.expanded_query:
                search_query = query_info.expanded_query
                logger.info(f"Usando consulta expandida: {search_query[:100]}..." if len(search_query) > 100 else search_query)
            
            # Log de información adicional disponible
            logger.info(f"Información adicional de la consulta:")
            logger.info(f"  Intención principal: {query_info.main_intent}")
            logger.info(f"  Complejidad: {query_info.complexity}")
            logger.info(f"  Entidades detectadas: {[f'{e.type}:{e.value}' for e in query_info.entities]}")
            logger.info(f"  Palabras clave: {[k.word for k in query_info.keywords]}")
        
        logger.info(f"Generando embedding para la consulta de búsqueda...")
        logger.info("=" * 80)
        
        # Primero obtenemos el embedding de la consulta (esto es un prerequisito para las búsquedas)
        start_time_embedding = time.time()
        query_embedding = await get_embedding(search_query, ctx.deps.openai_client)
        embedding_time = time.time() - start_time_embedding
        logger.info(f"Tiempo para generar embedding: {embedding_time:.2f}s")
        
        if not any(query_embedding):
            logger.warning("Received a zero embedding vector. Skipping search.")
            return "No relevant documentation found."
        
        # Definimos las funciones para cada método de búsqueda
        
        async def get_vector_chunks():
            """Recupera chunks por similitud vectorial."""
            start_time = time.time()
            logger.info(f"Buscando chunks por similitud vectorial (match_count={MAX_CHUNKS_RETURNED})")
            try:
                result = ctx.deps.supabase.rpc(
                    'match_pd_peru',
                    {
                        'query_embedding': query_embedding,
                        'match_count': MAX_CHUNKS_RETURNED
                    }
                ).execute()
                
                chunks = []
                matched_ids = set()
                cluster_ids = set()
                
                if result.data:
                    logger.info(f"Encontrados {len(result.data)} chunks por similitud vectorial")
                    
                    for doc in result.data:
                        chunk_text = f"""
# {doc['title']}

{doc['content']}
"""
                        chunks.append(chunk_text)
                        matched_ids.add(doc.get('id'))
                        
                        # Extraer cluster_ids
                        if 'metadata' in doc and doc['metadata'] and 'cluster_id' in doc['metadata']:
                            cluster_id = doc['metadata'].get('cluster_id')
                            if cluster_id is not None and cluster_id != -1:
                                cluster_ids.add(cluster_id)
                else:
                    logger.info("No relevant documentation found via vector search.")
                
                elapsed_time = time.time() - start_time
                logger.info(f"Tiempo de búsqueda vectorial: {elapsed_time:.2f}s")
                return chunks, matched_ids, cluster_ids
            except Exception as e:
                logger.error(f"Error en búsqueda vectorial: {e}")
                return [], set(), set()
        
        async def get_bm25_chunks(matched_ids):
            """
            Recupera chunks usando BM25 con EXACTAMENTE los mismos filtros que match_pd_peru RPC.
            """
            start_time = time.time()
            logger.info(f"Ejecutando búsqueda léxica BM25 (complementaria)")
            bm25_chunks = []
            new_matched_ids = matched_ids.copy()
            
            try:
                bm25_limit = 15
                # Incluir metadata en la consulta
                bm25_result = ctx.deps.supabase.table("pd_peru").select("""
                    id, title, summary, content, metadata""").execute()
                
                # APLICAR EXACTAMENTE LA MISMA LÓGICA QUE LA FUNCIÓN RPC
                filtered_docs = []
                for doc in bm25_result.data:
                    regulatory_doc = doc.get('regulatory_documents')
                    doc_metadata = doc.get('metadata', {}) or {}  # Asegurar que no sea None
                    chunk_status = doc_metadata.get('status')
                    
                    # EXACTAMENTE los mismos 3 casos que en match_pd_peru RPC
                    is_vigente = (
                        # Caso 1: Priorizar el status del documento principal si existe
                        (regulatory_doc and regulatory_doc.get('status') == 'vigente') 
                        or 
                        # Caso 2: Si no hay documento principal, verificar status en metadata del chunk
                        (regulatory_doc is None and chunk_status == 'vigente')
                        or
                        # Caso 3: Si no hay información de status en ningún lado, incluir el chunk
                        (regulatory_doc is None and chunk_status is None)
                    )
                    
                    if is_vigente:
                        filtered_docs.append(doc)
                    else:
                        # Log para debug
                        doc_status = regulatory_doc.get('status') if regulatory_doc else 'None'
                        logger.debug(f"BM25 excluyó chunk {doc.get('id')}: doc_status={doc_status}, chunk_status={chunk_status}")
                
                logger.info(f"BM25: {len(bm25_result.data)} chunks iniciales → {len(filtered_docs)} chunks después del filtro de vigencia")
                
                if filtered_docs:
                    # Verificar NLTK
                    try:
                        nltk.data.find('tokenizers/punkt')
                    except LookupError:
                        nltk.download('punkt', quiet=True, download_dir=nltk.data.path[0])
                    
                    corpus = []
                    id_map = []
                    full_docs = []
                    
                    for doc in filtered_docs:  # ← Usar filtered_docs en lugar de bm25_docs
                        # Para BM25, usar el contenido completo incluyendo metadata
                        text_parts = [
                            doc.get('title', ''),
                            doc.get('summary', ''),
                            doc.get('content', ''),
                            str(doc.get('metadata', ''))  # Convertir metadata a string para búsqueda
                        ]
                        text = ' '.join(filter(None, text_parts))  # Filtrar partes vacías
                        
                        tokens = word_tokenize(text.lower())
                        corpus.append(tokens)
                        id_map.append(doc.get('id'))
                        full_docs.append(doc)
                    
                    # Usar palabras clave de Query Understanding si están disponibles
                    if query_info and query_info.keywords:
                        important_keywords = [k.word for k in query_info.keywords if k.importance > 0.7]
                        if important_keywords:
                            logger.info(f"Usando palabras clave de alta importancia para BM25: {important_keywords}")
                            query_tokens = word_tokenize(" ".join(important_keywords).lower())
                        else:
                            query_tokens = word_tokenize(search_query.lower())
                    else:
                        query_tokens = word_tokenize(search_query.lower())
                    
                    bm25 = BM25Okapi(corpus)
                    scores = bm25.get_scores(query_tokens)
                    
                    best_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:bm25_limit]
                    
                    for i in best_indices:
                        if scores[i] > 0:
                            doc_id = id_map[i]
                            if doc_id not in new_matched_ids:
                                new_matched_ids.add(doc_id)
                                doc = full_docs[i]
                                
                                summary = doc.get('summary', '')
                                summary_section = f"\nResumen: {summary}\n" if summary else ""

                                bm25_text = f"""
        # {doc.get('title', '')} (Coincidencia de términos exactos)
        {summary_section}
        {doc.get('content', '')}
        """
                                bm25_chunks.append(bm25_text)
                                logger.debug(f"BM25 incluyó chunk {doc_id} con score {scores[i]:.3f}")
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"Recuperados {len(bm25_chunks)} chunks adicionales con BM25 en {elapsed_time:.2f}s")
            except Exception as e:
                logger.error(f"Error en la recuperación BM25: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                elapsed_time = time.time() - start_time
                logger.error(f"Tiempo hasta error BM25: {elapsed_time:.2f}s")
            
            return bm25_chunks
        
        # Si tenemos entidades de Query Understanding, podemos hacer una búsqueda adicional por entidades
        async def get_entity_based_chunks(matched_ids):
            """
            Recupera chunks basados en las entidades detectadas por Query Understanding.
            Solo se ejecuta si hay información de Query Understanding disponible.
            """
            if not query_info or not query_info.entities:
                return []
            
            start_time = time.time()
            logger.info(f"Ejecutando búsqueda basada en entidades")
            entity_chunks = []
            new_matched_ids = matched_ids.copy()
            
            try:
                # Extraer entidades relevantes (priorizar regulation, program, process)
                priority_types = ['regulation', 'program', 'process', 'technical_requirement']
                relevant_entities = [e for e in query_info.entities if e.type in priority_types]
                
                if not relevant_entities:
                    logger.info("No hay entidades de alta prioridad para búsqueda")
                    return []
                
                # Construir condiciones para la consulta SQL
                entity_conditions = []
                for entity in relevant_entities:
                    # Escapar valor para SQL y convertir a minúsculas para comparación insensible a mayúsculas
                    value = entity.value.lower().replace("'", "''")
                    entity_conditions.append(f"(LOWER(content) LIKE '%{value}%' OR LOWER(title) LIKE '%{value}%')")
                
                if not entity_conditions:
                    return []
                
                # Combinar condiciones con OR
                where_clause = " OR ".join(entity_conditions)
                
                # Ejecutar consulta en Supabase
                entity_query = ctx.deps.supabase.table("pd_peru").select("id, title, summary, content, article_references").filter(where_clause, False).execute()
                
                if entity_query.data:
                    for doc in entity_query.data:
                        doc_id = doc.get('id')
                        if doc_id not in new_matched_ids:
                            new_matched_ids.add(doc_id)
                            
                            summary = doc.get('summary', '')
                            summary_section = f"\nResumen: {summary}\n" if summary else ""
                            
                            entity_text = f"""
# {doc.get('title', '')} (Coincidencia por entidad específica)
{summary_section}
{doc.get('content', '')}
"""
                            entity_chunks.append(entity_text)
                
                elapsed_time = time.time() - start_time
                logger.info(f"Recuperados {len(entity_chunks)} chunks adicionales por entidades en {elapsed_time:.2f}s")
                return entity_chunks
                
            except Exception as e:
                logger.error(f"Error en la búsqueda por entidades: {e}")
                return []
        
        # Ejecutar búsqueda vectorial primero (necesitamos los cluster_ids)
        start_search_time = time.time()
        vector_chunks, matched_ids, cluster_ids = await get_vector_chunks()
        vector_time = time.time() - start_search_time
        
        # Luego ejecutamos en paralelo las búsquedas complementarias
        start_parallel_time = time.time()
        
        # Tareas asíncronas para las búsquedas complementarias
        tasks = [
            get_cluster_chunks(ctx, cluster_ids, matched_ids),  # Pasamos el contexto ctx como primer argumento
            get_bm25_chunks(matched_ids)
        ]
        
        # Si tenemos información de Query Understanding, agregamos la búsqueda por entidades
        if query_info and query_info.entities:
            tasks.append(get_entity_based_chunks(matched_ids))
        
        # Ejecutar todas las búsquedas en paralelo
        parallel_results = await asyncio.gather(*tasks)
        
        # Extraer resultados
        cluster_chunks_result = parallel_results[0]
        bm25_chunks = parallel_results[1]
        cluster_chunks, updated_matched_ids = cluster_chunks_result
        
        # Extraer chunks basados en entidades si existen
        entity_chunks = []
        if query_info and query_info.entities and len(parallel_results) > 2:
            entity_chunks = parallel_results[2]
        
        parallel_time = time.time() - start_parallel_time
        logger.info(f"Tiempo de búsquedas paralelas: {parallel_time:.2f}s")
        
        # Combinar todos los chunks
        all_chunks = vector_chunks + cluster_chunks + bm25_chunks + entity_chunks
        
        # Verificar si tenemos algún resultado
        if not all_chunks:
            logger.info("No relevant documentation found through any method.")
            return "No relevant documentation found."
        
        logger.info(f"RESUMEN: {len(vector_chunks)} chunks por similitud vectorial + {len(cluster_chunks)} chunks por cluster + {len(bm25_chunks)} chunks por BM25 + {len(entity_chunks)} chunks por entidades = {len(all_chunks)} chunks en total")
        
        # Tiempo para reranking
        start_rerank_time = time.time()
        try:
            # Aplicamos reranking con información de Query Understanding si está disponible
            if len(all_chunks) > 3:
                logger.info("Aplicando reranking con LLM...")
                logger.info(f"Usando modelo: {llm}")
                
                # Construir prompt de reranking enriquecido con información de Query Understanding
                reranking_query = search_query
                if query_info:
                    # Construir contexto enriquecido para el reranking
                    intent_context = f"Intención principal: {query_info.main_intent}" if query_info.main_intent else ""
                    entity_context = f"Entidades importantes: {', '.join([e.value for e in query_info.entities[:5]])}" if query_info.entities else ""
                    keyword_context = f"Palabras clave: {', '.join([k.word for k in query_info.keywords[:5]])}" if query_info.keywords else ""
                    
                    reranking_query = f"{search_query}\n\nContexto adicional:\n{intent_context}\n{entity_context}\n{keyword_context}"
                
                # Determinar cuántos chunks mantener según el tipo de consulta
                if query_info and query_info.complexity == "complex":
                    optimal_chunk_count = MAX_CHUNKS_TO_KEEP_REPORTS  # 12 para consultas complejas
                else:
                    # Verificar si es para reporte (puedes detectar esto de diferentes maneras)
                    # Por ejemplo, si la consulta menciona "reporte", "informe", "análisis detallado"
                    query_lower = search_query.lower()
                    is_for_report = any(keyword in query_lower for keyword in [
                        "reporte", "informe", "análisis detallado", "documento", 
                        "generar reporte", "crear informe", "análisis completo"
                    ])
                    
                    if is_for_report:
                        optimal_chunk_count = MAX_CHUNKS_TO_KEEP_REPORTS  # 12 para reportes
                    else:
                        optimal_chunk_count = MAX_CHUNKS_TO_KEEP_NORMAL   # 8 para consultas normales
                
                logger.info(f"Configuración: evaluar {MAX_CHUNKS_FOR_RERANKING} chunks con LLM, mantener {optimal_chunk_count} chunks finales")
                
                # Usar el reranking mejorado con límite configurable
                reranked_chunks = await rerank_chunks(
                    ctx, 
                    reranking_query, 
                    all_chunks, 
                    max_to_rerank=MAX_CHUNKS_FOR_RERANKING,  # Evaluar 15 con LLM
                    max_to_return=optimal_chunk_count,       # Devolver solo los óptimos
                    diversify=True
                )
                
                if reranked_chunks:  # Verificar que el resultado no sea vacío
                    all_chunks = reranked_chunks
                    logger.info(f"Reranking completado, {len(all_chunks)} chunks finales ordenados por relevancia")
                else:
                    logger.warning("El reranking no produjo resultados, manteniendo orden original")
                    # Aplicar límite manual si el reranking falló
                    if len(all_chunks) > optimal_chunk_count:
                        logger.info(f"Aplicando límite manual: {len(all_chunks)} -> {optimal_chunk_count} chunks")
                        all_chunks = all_chunks[:optimal_chunk_count]

        except Exception as e:
            logger.warning(f"No se pudo aplicar reranking con LLM: {e}")
            # Agregar más detalles sobre el error para facilitar el debugging
            logger.warning(f"Tipo de error: {type(e).__name__}")
            logger.warning(f"Detalles completos del error: {str(e)}")
            # Si el reranking falla, continuamos con el orden original de chunks
        
        rerank_time = time.time() - start_rerank_time
        logger.info(f"Tiempo de reranking: {rerank_time:.2f}s")
        
        # Proceso final: combinación y truncamiento
        start_final_time = time.time()
        combined_text = "\n\n---\n\n".join(all_chunks)
        total_tokens = count_tokens(combined_text, llm)
        logger.info(f"Total tokens en todos los chunks: {total_tokens}")
        
        # Truncar si es necesario
        if total_tokens > MAX_TOTAL_TOKENS:
            logger.info(f"El contenido combinado excede el límite de tokens ({total_tokens} > {MAX_TOTAL_TOKENS}). Se realizará truncamiento.")
            truncated_chunks = []
            accumulated_tokens = 0
            chunks_included = 0
            for chunk in all_chunks:
                chunk_tokens = count_tokens(chunk, llm)
                if accumulated_tokens + chunk_tokens > MAX_TOTAL_TOKENS:
                    remaining_tokens = MAX_TOTAL_TOKENS - accumulated_tokens
                    truncated_chunk = truncate_text(chunk, remaining_tokens, llm)
                    truncated_chunks.append(truncated_chunk)
                    chunks_included += 1
                    logger.debug(f"Chunk #{chunks_included} truncado para caber en el límite de tokens")
                    break
                else:
                    truncated_chunks.append(chunk)
                    accumulated_tokens += chunk_tokens
                    chunks_included += 1
            
            combined_text = "\n\n---\n\n".join(truncated_chunks)
            logger.info(f"Después de truncar: {chunks_included} chunks incluidos, {count_tokens(combined_text, llm)} tokens totales")
        
        final_time = time.time() - start_final_time
        total_time = time.time() - start_time_total
        
        # Resumen de tiempos
        logger.info("==== RESUMEN DE TIEMPOS ====")
        logger.info(f"Generación de embedding: {embedding_time:.2f}s")
        logger.info(f"Búsqueda vectorial: {vector_time:.2f}s")
        logger.info(f"Búsquedas paralelas: {parallel_time:.2f}s")
        logger.info(f"Reranking: {rerank_time:.2f}s")
        logger.info(f"Combinación y truncamiento: {final_time:.2f}s")
        logger.info(f"TIEMPO TOTAL: {total_time:.2f}s")
        logger.info("==========================")
        
        # Si tenemos información de Query Understanding, agregamos metadatos al resultado
        if query_info:
            # Agregar un separador con información sobre la consulta
            metadata_header = f"""
=== INFORMACIÓN DE ANÁLISIS DE CONSULTA ===
Intención principal: {query_info.main_intent}
Complejidad: {query_info.complexity}
Entidades detectadas: {[f'{e.type}:{e.value}' for e in query_info.entities]}
Consulta utilizada para búsqueda: {search_query[:100]}..." if len(search_query) > 100 else search_query
===========================================

"""
            combined_text = metadata_header + combined_text
        
        mark_tool_as_executed(tool_name, query_hash, combined_text)
        return combined_text
    
    except Exception as e:
        total_time = time.time() - start_time_total
        logger.error(f"Error retrieving documentation en {total_time:.2f}s: {e}")
        return f"Error retrieving documentation: {str(e)}"

        mark_tool_as_executed(tool_name, query_hash, error_result)
        
        # NUEVO: Usar modelo de razonamiento si está configurado
        if llm_reasoning and (llm_reasoning.startswith("gpt-5") or llm_reasoning.startswith("o1")):
            logger.info("Usando modelo de razonamiento para procesar la documentación recuperada")
            
            try:
                reasoning_response = await call_reasoning_model(
                    prompt=f"Consulta del usuario: {user_query}",
                    retrieved_context=combined_text,
                    openai_client=ctx.deps.openai_client,
                    model=llm_reasoning
                )
                
                # Combinar la respuesta del modelo de razonamiento con el contexto
                final_response = f"""ANÁLISIS CON MODELO DE RAZONAMIENTO:

{reasoning_response}

---

DOCUMENTACIÓN DE REFERENCIA:
{combined_text}"""
                
                mark_tool_as_executed(tool_name, query_hash, final_response)
                return final_response
                
            except Exception as e:
                logger.error(f"Error usando modelo de razonamiento, devolviendo documentación sin procesar: {e}")
                mark_tool_as_executed(tool_name, query_hash, combined_text)
                return combined_text
        else:
            # Comportamiento normal sin modelo de razonamiento
            mark_tool_as_executed(tool_name, query_hash, combined_text)
            return combined_text


@ai_expert.tool
async def perform_gap_analysis(ctx: RunContext[AIDeps], policy_text: str, focus_areas: Optional[str] = None) -> str:
    """
    Realiza un análisis GAP detallado entre una política interna y la normativa aplicable.
    
    Args:
        policy_text: El texto completo de la política a evaluar
        focus_areas: Áreas específicas a evaluar (opcional): "consentimiento, derechos ARCO, seguridad", etc.
    
    Returns:
        Análisis GAP completo en formato Markdown con brechas identificadas y recomendaciones
    """
    logger.info("HERRAMIENTA INVOCADA: perform_gap_analysis")
    
    try:
        # Construir consulta de búsqueda
        search_query = "normativa protección datos privacidad requisitos obligatorios derechos seguridad"
        if focus_areas:
            search_query += f" {focus_areas}"
        
        logger.info(f"Recuperando documentación normativa para GAP analysis...")
        
        # Reutilizar COMPLETAMENTE la función existente
        regulatory_docs = await retrieve_relevant_documentation(ctx, search_query)
        
        if not regulatory_docs or regulatory_docs == "No relevant documentation found.":
            return "No se pudo recuperar documentación normativa suficiente para realizar el análisis GAP."
        
        # Prompt simplificado sin iconos
        gap_prompt = f"""
Realiza un análisis GAP profesional y detallado (mínimo 4.000 palabras) comparando la política interna con la normativa aplicable.

POLÍTICA A EVALUAR:
{policy_text[:8000]}

NORMATIVA DE REFERENCIA:
{regulatory_docs}

ESTRUCTURA REQUERIDA:

## Resumen Ejecutivo
- Política evaluada: [Identificar tipo y alcance]
- Total de brechas: [Número] (Alto: X, Medio: Y, Bajo: Z)
- Nivel de cumplimiento: [Porcentaje estimado]
- Recomendación principal: [Acción más crítica]

## Análisis Detallado de Brechas

### GAP-001: [Nombre descriptivo]
- **Descripción:** [Qué no cumple la política]
- **Requisito normativo:** [Artículo específico de la documentación]
- **Estado actual:** [Cómo aborda este tema la política actual]
- **Nivel de riesgo:** [Alto/Medio/Bajo] - [Justificación]
- **Área impactada:** [Departamento/función]
- **Recomendación:** [Acción específica con texto sugerido]
- **Esfuerzo:** [Alto/Medio/Bajo] - [Justificación]

[Continuar con GAP-002, GAP-003, etc. - MÍNIMO 8 brechas]

## Matriz de Priorización

| ID | Brecha | Riesgo | Esfuerzo | Prioridad | Plazo |
|----|--------|--------|----------|-----------|--------|
| GAP-001 | [Resumen] | Alto | Medio | 1 | 15 días |
| GAP-002 | [Resumen] | Medio | Bajo | 2 | 30 días |

## Plan de Implementación

### Fase 1: Crítico (0-30 días)
- [Brechas de alto riesgo con acciones específicas]

### Fase 2: Importante (30-90 días)  
- [Brechas de riesgo medio]

### Fase 3: Mejoras (90+ días)
- [Brechas de bajo riesgo y optimizaciones]

## Métricas de Seguimiento
- [KPIs específicos para medir progreso]

INSTRUCCIONES CRÍTICAS:
1. Identificar AL MENOS 8-10 brechas específicas
2. Citar SOLO artículos presentes en la documentación normativa proporcionada
3. Ser específico en recomendaciones (incluir texto exacto a añadir/modificar)
4. Justificar cada nivel de riesgo con criterios objetivos
5. Proporcionar estimaciones realistas de tiempo y esfuerzo
6. Incluir consideraciones prácticas de implementación

Enfócate en crear un análisis accionable y profesional.
"""

        # Ejecutar análisis
        response = await ctx.deps.openai_client.respones.create(
            model=llm,
            messages=[{"role": "user", "content": gap_prompt}],
            temperature=0.2,
            max_tokens=12000
        )
        
        gap_result = response.choices[0].message.content
        
        # Verificar que tenemos contenido válido
        if not gap_result or len(gap_result.strip()) < 50:
            logger.error("GAP analysis produjo resultado vacío o muy corto")
            return "Error: El análisis GAP no pudo generar un resultado completo. La documentación fue recuperada correctamente, pero el procesamiento final falló."
        
        # Añadir disclaimer simple
        gap_result += "\n\n---\n\n*Este análisis GAP se basa exclusivamente en la documentación normativa consultada y no constituye asesoramiento legal definitivo.*"
        
        logger.info(f"GAP analysis completado exitosamente. Longitud del resultado: {len(gap_result)} caracteres")
        return gap_result

    except Exception as e:
        logger.error(f"Error en perform_gap_analysis: {str(e)}")
        return f"Error al realizar el análisis GAP: {str(e)}"