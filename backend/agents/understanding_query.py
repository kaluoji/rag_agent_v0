# =========================== INICIO DEL CÓDIGO DEL AGENTE ===========================

from __future__ import annotations as _annotations

import logfire
import asyncio
import logging
import time
import json
import re
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from openai import AsyncOpenAI
from supabase import Client

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel

from app.core.config import settings
from utils.utils import count_tokens, truncate_text

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = settings.llm_model
tokenizer_model = settings.tokenizer_model
model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

class Intent(BaseModel):
    """Información sobre una intención detectada en la consulta."""
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    description: str = ""

class Entity(BaseModel):
    """Entidad detectada en la consulta."""
    type: str
    value: str
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Keyword(BaseModel):
    """Palabra clave relevante identificada en la consulta."""
    word: str
    importance: float = Field(ge=0.0, le=1.0, default=1.0)
    related_terms: List[str] = Field(default_factory=list)

class SubQuery(BaseModel):
    """Subconsulta generada a partir de una consulta compleja."""
    text: str
    intent: Optional[str] = None
    focus: str = ""
    requires_information_from: List[str] = Field(default_factory=list)

class QueryInfo(BaseModel):
    """Estructura que contiene la información procesada de una consulta."""
    original_query: str
    expanded_query: str = ""
    decomposed_queries: List[SubQuery] = Field(default_factory=list)
    intents: List[Intent] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    keywords: List[Keyword] = Field(default_factory=list)
    domain_terms: Dict[str, str] = Field(default_factory=dict)
    language: str = "es"
    complexity: str = Field("simple", description="Nivel de complejidad de la consulta: simple, medium, complex")
    search_query: str = ""
    estimated_search_quality: float = Field(0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def main_intent(self) -> Optional[str]:
        """Devuelve la intención principal si existe."""
        if not self.intents:
            return None
        return sorted(self.intents, key=lambda x: x.confidence, reverse=True)[0].name
    
    @property
    def confidence(self) -> float:
        """Devuelve la confianza en la intención principal."""
        if not self.intents:
            return 0.0
        return sorted(self.intents, key=lambda x: x.confidence, reverse=True)[0].confidence
    
    @property
    def entity_values(self) -> Dict[str, List[str]]:
        """Devuelve un diccionario con los valores de entidades agrupados por tipo."""
        result = {}
        for entity in self.entities:
            if entity.type not in result:
                result[entity.type] = []
            result[entity.type].append(entity.value)
        return result
    
    @property
    def keyword_list(self) -> List[str]:
        """Devuelve una lista simple de palabras clave."""
        return [k.word for k in self.keywords]
    
    def to_search_context(self) -> Dict[str, Any]:
        """Convierte la información de la consulta en un contexto de búsqueda útil."""
        return {
            "query": self.search_query or self.expanded_query or self.original_query,
            "keywords": self.keyword_list,
            "entities": self.entity_values,
            "domain_terms": list(self.domain_terms.keys()),
            "language": self.language,
            "complexity": self.complexity
        }

class QueryUnderstandingDeps(BaseModel):
    """Dependencias necesarias para el agente de comprensión de consultas."""
    supabase: Client
    openai_client: AsyncOpenAI

    class Config:
        arbitrary_types_allowed = True

# CORRECCIÓN: Prompt simplificado que devuelve estructura JSON completa
system_prompt = """
Eres un agente especializado en analizar consultas sobre normativas y regulaciones de cualquier sector e industria.

Tu tarea es procesar la consulta del usuario y devolver un análisis completo en formato JSON estructurado.

ANALIZA CADA CONSULTA PARA:

1. **IDENTIFICAR** entidades relevantes (regulaciones, artículos, jurisdicciones, autoridades, plazos, sectores)
2. **CLASIFICAR** el tipo de consulta (informativa, comparativa, procedimental, interpretativa, actualización)
3. **EXTRAER** palabras clave esenciales para búsqueda
4. **DETERMINAR** complejidad (simple, medium, complex)
5. **REFORMULAR** la consulta para mejorar claridad

DIRECTRICES:
- NO inventes entidades que no estén mencionadas
- Si hay ambigüedad, reconócela
- Mantén el significado original al reformular
- Usa solo información explícita en la consulta

RESPONDE SIEMPRE con este formato JSON exacto:
{
  "language": "es",
  "entities": [
    {"type": "regulation", "value": "nombre_regulacion"},
    {"type": "region", "value": "jurisdiccion"}
  ],
  "keywords": [
    {"word": "palabra_clave", "importance": 0.9}
  ],
  "intents": [
    {"name": "tipo_consulta", "confidence": 0.9, "description": "descripción"}
  ],
  "complexity": "simple|medium|complex",
  "expanded_query": "consulta reformulada y expandida",
  "search_query": "consulta optimizada para búsqueda",
  "domain_terms": {
    "término_técnico": "definición"
  },
  "estimated_search_quality": 0.8
}
"""

query_understanding_agent = Agent(
    model=model,
    system_prompt=system_prompt,
    deps_type=QueryUnderstandingDeps,
    retries=2
)

# CORRECCIÓN: Herramienta principal simplificada que devuelve JSON estructurado
@query_understanding_agent.tool
async def analyze_complete_query(ctx: RunContext[QueryUnderstandingDeps], query: str) -> Dict[str, Any]:
    """
    Analiza completamente una consulta y devuelve toda la información estructurada.
    
    Esta herramienta reemplaza las múltiples herramientas individuales para evitar
    problemas de coordinación y asegurar un resultado consistente.
    """
    logger.info(f"Ejecutando análisis completo de: {query[:100]}...")
    
    try:
        # Usar el cliente OpenAI directamente para un control más preciso
        completion = await ctx.deps.openai_client.chat.completions.create(
            model=llm,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analiza esta consulta: {query}"}
            ]
        )
        
        # Parsear el resultado JSON
        result_json = json.loads(completion.choices[0].message.content)
        logger.info("Análisis completo ejecutado exitosamente")
        
        return result_json
        
    except Exception as e:
        logger.error(f"Error en análisis completo: {e}")
        # Devolver estructura mínima en caso de error
        return {
            "language": "es",
            "entities": [],
            "keywords": [{"word": query.split()[0] if query.split() else "consulta", "importance": 0.5}],
            "intents": [{"name": "consulta_general", "confidence": 0.5, "description": "Consulta general por error en análisis"}],
            "complexity": "simple",
            "expanded_query": query,
            "search_query": query,
            "domain_terms": {},
            "estimated_search_quality": 0.5
        }

# CORRECCIÓN: Funciones auxiliares simplificadas para procesamiento básico
async def analyze_query_basic(openai_client: AsyncOpenAI, query: str) -> Dict[str, Any]:
    """
    Versión simplificada del análisis para consultas que no requieren procesamiento complejo.
    """
    logger.info("Ejecutando análisis básico")
    
    try:
        completion = await openai_client.chat.completions.create(
            model=llm,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": """
Analiza esta consulta sobre normativas y regulaciones y devuelve información básica en JSON:

{
  "language": "es",
  "entities": [{"type": "tipo", "value": "valor"}],
  "keywords": [{"word": "palabra", "importance": 0.8}],
  "intents": [{"name": "tipo_consulta", "confidence": 0.9}],
  "complexity": "simple",
  "search_query": "consulta optimizada"
}
"""},
                {"role": "user", "content": query}
            ]
        )
        
        result = json.loads(completion.choices[0].message.content)
        logger.info("Análisis básico completado")
        return result
        
    except Exception as e:
        logger.error(f"Error en análisis básico: {e}")
        return {
            "language": "es",
            "entities": [],
            "keywords": [{"word": "consulta", "importance": 0.5}],
            "intents": [{"name": "consulta_general", "confidence": 0.5}],
            "complexity": "simple",
            "search_query": query
        }

def map_dict_to_query_info(data: Dict[str, Any], original_query: str) -> QueryInfo:
    """
    Mapea un diccionario de datos a un objeto QueryInfo de manera segura.
    """
    logger.info("Mapeando diccionario a QueryInfo")
    
    try:
        # Crear el objeto QueryInfo base
        query_info = QueryInfo(original_query=original_query)
        
        # Mapear campos básicos
        query_info.language = data.get('language', 'es')
        query_info.complexity = data.get('complexity', 'simple')
        query_info.expanded_query = data.get('expanded_query', original_query)
        query_info.search_query = data.get('search_query', original_query)
        query_info.estimated_search_quality = data.get('estimated_search_quality', 0.5)
        query_info.domain_terms = data.get('domain_terms', {})
        
        # Mapear entidades
        entities_data = data.get('entities', [])
        for entity_dict in entities_data:
            if isinstance(entity_dict, dict) and 'type' in entity_dict and 'value' in entity_dict:
                entity = Entity(
                    type=entity_dict['type'],
                    value=entity_dict['value'],
                    metadata=entity_dict.get('metadata', {})
                )
                query_info.entities.append(entity)
        
        # Mapear palabras clave
        keywords_data = data.get('keywords', [])
        for keyword_dict in keywords_data:
            if isinstance(keyword_dict, dict) and 'word' in keyword_dict:
                keyword = Keyword(
                    word=keyword_dict['word'],
                    importance=keyword_dict.get('importance', 0.8),
                    related_terms=keyword_dict.get('related_terms', [])
                )
                query_info.keywords.append(keyword)
        
        # Mapear intenciones
        intents_data = data.get('intents', [])
        for intent_dict in intents_data:
            if isinstance(intent_dict, dict) and 'name' in intent_dict:
                intent = Intent(
                    name=intent_dict['name'],
                    confidence=intent_dict.get('confidence', 0.5),
                    description=intent_dict.get('description', '')
                )
                query_info.intents.append(intent)
        
        logger.info(f"Mapeo completado: {len(query_info.entities)} entidades, {len(query_info.keywords)} palabras clave, {len(query_info.intents)} intenciones")
        return query_info
        
    except Exception as e:
        logger.error(f"Error mapeando datos: {e}")
        # Devolver un QueryInfo mínimo pero válido
        return QueryInfo(
            original_query=original_query,
            complexity="simple",
            search_query=original_query
        )

async def evaluate_query_complexity(query: str, openai_client: AsyncOpenAI) -> bool:
    """
    Evalúa rápidamente si una consulta es compleja y necesita procesamiento avanzado.
    """
    logger.info("Evaluando complejidad básica de la consulta")
    
    try:
        # Criterios simples primero
        words = query.split()
        word_count = len(words)
        question_count = query.count('?')
        
        logger.info(f"Criterios básicos: {word_count} palabras, {question_count} signos de pregunta")

        # Si es claramente compleja por criterios básicos
        if word_count > 20 or question_count > 1:
            logger.info("Consulta clasificada como compleja por criterios básicos")
            return True
            
        # Si es claramente simple
        if word_count <= 10 and question_count <= 1:
            logger.info("Consulta clasificada como simple por criterios básicos")
            return False
            
        # Para casos ambiguos, usar el modelo
        completion = await openai_client.chat.completions.create(
            model=llm,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": """Evalúa si esta consulta sobre normativas es compleja.
                Compleja = múltiples preguntas, varios temas, requiere análisis profundo.
                Simple = una pregunta directa, un tema claro.
                Responde: {"is_complex": true/false, "reason": "explicación"}"""},
                {"role": "user", "content": query}
            ]
        )
        
        result = json.loads(completion.choices[0].message.content)
        is_complex = result.get("is_complex", False)
        
        logger.info(f"Evaluación con modelo: {'compleja' if is_complex else 'simple'} - {result.get('reason', '')}")
        return is_complex
        
    except Exception as e:
        logger.error(f"Error evaluando complejidad: {e}")
        # En caso de error, asumir que no es compleja para evitar problemas
        return False

# CORRECCIÓN: Función principal simplificada y robusta
async def process_query(query: str, deps: QueryUnderstandingDeps) -> QueryInfo:
    """
    Procesa una consulta de manera adaptativa y robusta.
    """
    start_time = time.time()
    logger.info(f"Iniciando procesamiento de consulta: {query[:100]}...")
    
    try:
        # Evaluar complejidad
        is_complex = await evaluate_query_complexity(query, deps.openai_client)
        processing_mode = "full" if is_complex else "basic"
        
        logger.info(f"Consulta clasificada como: {'compleja' if is_complex else 'simple'}")
        logger.info(f"Modo de procesamiento: {processing_mode}")
        
        # Procesar según complejidad
        if processing_mode == "basic":
            # Procesamiento básico directo
            logger.info("Ejecutando procesamiento básico")
            analysis_data = await analyze_query_basic(deps.openai_client, query)
            query_info = map_dict_to_query_info(analysis_data, query)
            
        else:
            # Procesamiento completo con el agente
            logger.info("Ejecutando procesamiento completo con agente")
            try:
                result = await query_understanding_agent.run(
                    f"Analiza completamente esta consulta: {query}",
                    deps=deps
                )
                
                # CORRECCIÓN: Manejo robusto del resultado del agente
                if hasattr(result, 'data'):
                    agent_data = result.data
                    logger.info(f"Resultado del agente obtenido - Tipo: {type(agent_data)}")
                    
                    if isinstance(agent_data, dict):
                        # Si es un diccionario, mapear directamente
                        query_info = map_dict_to_query_info(agent_data, query)
                        logger.info("Datos del agente mapeados directamente")
                        
                    elif isinstance(agent_data, str):
                        # Si es string, intentar extraer JSON
                        logger.info("Resultado es string, intentando extraer JSON")
                        try:
                            # Buscar JSON en el texto
                            json_match = re.search(r'\{.*\}', agent_data, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(0)
                                parsed_data = json.loads(json_str)  # CORRECCIÓN: Variable definida correctamente
                                query_info = map_dict_to_query_info(parsed_data, query)
                                logger.info("JSON extraído y mapeado exitosamente")
                            else:
                                logger.warning("No se encontró JSON válido en la respuesta del agente")
                                raise ValueError("No JSON found")
                                
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.error(f"Error parseando JSON del agente: {e}")
                            # Fallback a procesamiento básico
                            logger.info("Fallback a procesamiento básico")
                            analysis_data = await analyze_query_basic(deps.openai_client, query)
                            query_info = map_dict_to_query_info(analysis_data, query)
                    
                    elif isinstance(agent_data, QueryInfo):
                        # Si ya es un QueryInfo, usar directamente
                        query_info = agent_data
                        logger.info("Resultado ya es QueryInfo")
                        
                    else:
                        logger.warning(f"Tipo de resultado inesperado: {type(agent_data)}")
                        # Fallback a procesamiento básico
                        analysis_data = await analyze_query_basic(deps.openai_client, query)
                        query_info = map_dict_to_query_info(analysis_data, query)
                        
                else:
                    logger.warning("El resultado del agente no tiene atributo 'data'")
                    # Fallback a procesamiento básico
                    analysis_data = await analyze_query_basic(deps.openai_client, query)
                    query_info = map_dict_to_query_info(analysis_data, query)
                    
            except Exception as agent_error:
                logger.error(f"Error con el agente de comprensión: {agent_error}")
                # Fallback a procesamiento básico
                logger.info("Fallback a procesamiento básico debido a error del agente")
                analysis_data = await analyze_query_basic(deps.openai_client, query)
                query_info = map_dict_to_query_info(analysis_data, query)
        
        # Validar y completar campos faltantes
        if not query_info.search_query:
            query_info.search_query = query_info.expanded_query or query
        
        if not query_info.expanded_query:
            query_info.expanded_query = query
            
        # Registrar métricas de tiempo
        elapsed_time = time.time() - start_time
        query_info.metadata["processing_time"] = elapsed_time
        query_info.metadata["processing_mode"] = processing_mode
        
        logger.info(f"Procesamiento completado en {elapsed_time:.2f}s")
        logger.info(f"Resultado final: {len(query_info.entities)} entidades, {len(query_info.keywords)} palabras clave")
        
        return query_info
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error crítico en procesamiento después de {elapsed_time:.2f}s: {e}")
        
        # Crear QueryInfo mínimo pero funcional en caso de error crítico
        fallback_query_info = QueryInfo(
            original_query=query,
            expanded_query=query,
            search_query=query,
            complexity="simple",
            language="es",
            estimated_search_quality=0.3,
            metadata={
                "error": str(e),
                "processing_time": elapsed_time,
                "processing_mode": "fallback"
            }
        )
        
        # Agregar al menos una palabra clave básica
        if query.strip():
            primary_word = query.split()[0] if query.split() else "consulta"
            fallback_query_info.keywords.append(
                Keyword(word=primary_word, importance=0.5)
            )
        
        # Agregar intención genérica
        fallback_query_info.intents.append(
            Intent(name="consulta_general", confidence=0.5, description="Intención por defecto debido a error")
        )
        
        logger.info("Devolviendo QueryInfo de fallback")
        return fallback_query_info


# ==================== FUNCIONES DE COMPATIBILIDAD ====================
# Estas funciones mantienen la compatibilidad con código existente

async def analyze_query_intent(ctx: RunContext[QueryUnderstandingDeps], query: str) -> List[Intent]:
    """
    DEPRECATED: Mantenida para compatibilidad. 
    Usa process_query() en su lugar.
    """
    logger.warning("Función analyze_query_intent está deprecada. Usa process_query() en su lugar.")
    
    try:
        completion = await ctx.deps.openai_client.chat.completions.create(
            model=llm,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": """Identifica la intención principal de la consulta sobre normativas.
                Responde con JSON: {"intents": [{"name": "tipo", "confidence": 0.9, "description": "desc"}]}"""},
                {"role": "user", "content": query}
            ]
        )
        
        result_json = json.loads(completion.choices[0].message.content)
        intents_data = result_json.get("intents", [])
        
        return [Intent(**intent_data) for intent_data in intents_data]
        
    except Exception as e:
        logger.error(f"Error en analyze_query_intent: {e}")
        return [Intent(name="consulta_general", confidence=0.5)]


async def extract_entities(ctx: RunContext[QueryUnderstandingDeps], text: str) -> List[Entity]:
    """
    DEPRECATED: Mantenida para compatibilidad.
    Usa process_query() en su lugar.
    """
    logger.warning("Función extract_entities está deprecada. Usa process_query() en su lugar.")
    
    try:
        completion = await ctx.deps.openai_client.chat.completions.create(
            model=llm,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": """Extrae entidades de normativas del texto.
                Responde con JSON: {"entities": [{"type": "tipo", "value": "valor"}]}"""},
                {"role": "user", "content": text}
            ]
        )
        
        result_json = json.loads(completion.choices[0].message.content)
        entities_data = result_json.get("entities", [])
        
        return [Entity(**entity_data) for entity_data in entities_data]
        
    except Exception as e:
        logger.error(f"Error en extract_entities: {e}")
        return []


async def extract_keywords(ctx: RunContext[QueryUnderstandingDeps], text: str) -> List[Keyword]:
    """
    DEPRECATED: Mantenida para compatibilidad.
    Usa process_query() en su lugar.
    """
    logger.warning("Función extract_keywords está deprecada. Usa process_query() en su lugar.")
    
    try:
        completion = await ctx.deps.openai_client.chat.completions.create(
            model=llm,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": """Extrae palabras clave relevantes del texto.
                Responde con JSON: {"keywords": [{"word": "palabra", "importance": 0.8}]}"""},
                {"role": "user", "content": text}
            ]
        )
        
        result_json = json.loads(completion.choices[0].message.content)
        keywords_data = result_json.get("keywords", [])
        
        return [Keyword(**keyword_data) for keyword_data in keywords_data]
        
    except Exception as e:
        logger.error(f"Error en extract_keywords: {e}")
        return []


# ==================== FUNCIONES AUXILIARES ADICIONALES ====================

def validate_query_info(query_info: QueryInfo) -> QueryInfo:
    """
    Valida y corrige un objeto QueryInfo para asegurar que tenga datos mínimos válidos.
    """
    logger.info("Validando QueryInfo")
    
    # Asegurar que hay al menos una palabra clave
    if not query_info.keywords and query_info.original_query.strip():
        primary_word = query_info.original_query.split()[0]
        query_info.keywords.append(Keyword(word=primary_word, importance=0.7))
        logger.info(f"Agregada palabra clave mínima: {primary_word}")
    
    # Asegurar que hay al menos una intención
    if not query_info.intents:
        query_info.intents.append(Intent(name="consulta_general", confidence=0.6))
        logger.info("Agregada intención mínima: consulta_general")
    
    # Asegurar que search_query no esté vacío
    if not query_info.search_query:
        query_info.search_query = query_info.expanded_query or query_info.original_query
        logger.info("Asignada search_query desde expanded_query o original_query")
    
    # Asegurar que expanded_query no esté vacío
    if not query_info.expanded_query:
        query_info.expanded_query = query_info.original_query
        logger.info("Asignada expanded_query desde original_query")
    
    # Validar estimated_search_quality
    if query_info.estimated_search_quality <= 0:
        # Calcular calidad estimada basada en la información disponible
        quality_score = 0.5  # Base
        if query_info.entities:
            quality_score += 0.2
        if len(query_info.keywords) > 2:
            quality_score += 0.2
        if query_info.complexity != "simple":
            quality_score += 0.1
        
        query_info.estimated_search_quality = min(quality_score, 1.0)
        logger.info(f"Calculada estimated_search_quality: {query_info.estimated_search_quality}")
    
    logger.info("Validación de QueryInfo completada")
    return query_info


async def test_query_understanding(deps: QueryUnderstandingDeps, test_queries: List[str]) -> None:
    """
    Función de testing para verificar que el agente de comprensión funciona correctamente.
    """
    logger.info(f"Iniciando test con {len(test_queries)} consultas")
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"TEST {i}/{len(test_queries)}: {query[:100]}...")
        
        try:
            start_time = time.time()
            result = await process_query(query, deps)
            elapsed_time = time.time() - start_time
            
            # Verificar que el resultado es válido
            assert isinstance(result, QueryInfo), f"Resultado no es QueryInfo: {type(result)}"
            assert result.original_query == query, "Original query no coincide"
            assert result.search_query, "Search query está vacío"
            assert result.complexity in ["simple", "medium", "complex"], f"Complejidad inválida: {result.complexity}"
            
            logger.info(f"✅ TEST {i} EXITOSO en {elapsed_time:.2f}s")
            logger.info(f"   - Entidades: {len(result.entities)}")
            logger.info(f"   - Palabras clave: {len(result.keywords)}")
            logger.info(f"   - Intenciones: {len(result.intents)}")
            logger.info(f"   - Complejidad: {result.complexity}")
            
        except Exception as e:
            logger.error(f"❌ TEST {i} FALLÓ: {e}")
            raise
    
    logger.info(f"\n{'='*50}")
    logger.info("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")


# ==================== FUNCIÓN PRINCIPAL DE ENTRADA ====================

async def understand_query(query: str, deps: QueryUnderstandingDeps) -> QueryInfo:
    """
    Función principal de entrada para el análisis de comprensión de consultas.
    
    Esta es la función que debes usar desde otros módulos en lugar de process_query().
    Incluye validación adicional y manejo de errores robusto.
    
    Args:
        query: La consulta del usuario a analizar
        deps: Dependencias necesarias (cliente OpenAI, Supabase, etc.)
    
    Returns:
        QueryInfo: Objeto con toda la información procesada de la consulta
    """
    logger.info("=== INICIANDO COMPRENSIÓN DE CONSULTA ===")
    
    # Validar entrada
    if not query or not query.strip():
        logger.error("Consulta vacía o inválida")
        return QueryInfo(
            original_query=query or "",
            search_query="consulta vacía",
            complexity="simple",
            metadata={"error": "Consulta vacía"}
        )
    
    # Procesar la consulta
    result = await process_query(query.strip(), deps)
    
    # Validar y corregir el resultado
    result = validate_query_info(result)
    
    logger.info("=== COMPRENSIÓN DE CONSULTA COMPLETADA ===")
    return result


# ==================== EXPORT DE FUNCIONES PRINCIPALES ====================

__all__ = [
    "QueryInfo",
    "Intent", 
    "Entity",
    "Keyword",
    "SubQuery",
    "QueryUnderstandingDeps",
    "understand_query",  # Función principal recomendada
    "process_query",     # Función interna, usar understand_query() en su lugar
    "test_query_understanding",
    "validate_query_info"
]

# =========================== FIN DEL CÓDIGO DEL AGENTE ===========================