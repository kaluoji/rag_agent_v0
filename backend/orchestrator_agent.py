from __future__ import annotations as _annotations

import logging
import json
import httpx
import os
from enum import Enum
from typing import List, Dict, Optional, Union, Any, Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from supabase import Client

from app.core.config import settings
from agents.ai_expert_v1 import ai_expert, AIDeps, debug_run_agent
from agents.understanding_query import process_query as process_query_understanding, QueryUnderstandingDeps, QueryInfo
from agents.report_agent import report_agent, ReportDeps, process_report_query
#from agents.web_scraping_agent import web_scraping_agent, WebScrapingDeps
#from agents.risk_assessment_agent import risk_assessment_agent, RiskAssessmentDeps
#from agents.normative_report_agent import normative_report_agent, ReportDeps as NormativeReportDeps, process_report_query

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización del modelo
llm = settings.llm_model
model = OpenAIModel(
    llm
)

class AgentType(str, Enum):
    """Tipos de agentes disponibles en el sistema."""
    COMPLIANCE = "compliance"
    QUERY_UNDERSTANDING = "query_understanding"
    REPORT = "report"
    #WEB_SCRAPING = "web_scraping"
    #RISK_ASSESSMENT = "risk_assessment"
    #NORMATIVE_REPORT = "normative_report"
    

class OrchestratorDeps(BaseModel):
    """Dependencias necesarias para el agente orquestador."""
    supabase: Client
    openai_client: AsyncOpenAI

    class Config:
        arbitrary_types_allowed = True

class AgentInfo(BaseModel):
    """Información sobre un agente detectado en la consulta."""
    agent_type: AgentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    query_parameters: Dict[str, Any] = {}

class OrchestratorPlan(BaseModel):
    """Plan de ejecución generado por el orquestador."""
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    requires_query_understanding: bool = False
    requires_complex_handling: bool = False
    primary_agent: AgentType
    additional_info: Dict[str, Any] = Field(default_factory=dict)

class OrchestrationResult(BaseModel):
    """Resultado de la orquestación."""
    agent_used: AgentType
    response: Any
    query_info: Optional[QueryInfo] = None
    additional_info: Optional[Dict[str, Any]] = None

system_prompt = """
Eres un agente orquestador encargado de coordinar múltiples agentes especializados en normativas y regulaciones de cualquier sector e industria. Tu objetivo principal es:

1. Determinar qué agentes deben involucrarse en la respuesta a una consulta
2. Planificar el flujo de trabajo necesario para responder a la consulta
3. Especificar los parámetros o información adicional para cada agente

Agentes disponibles:

1. QUERY_UNDERSTANDING
   - Especializado en analizar y procesar consultas de usuario
   - Expande consultas con términos implícitos
   - Descompone consultas complejas en sub-consultas
   - Identifica entidades e intenciones en la consulta
   - Detecta idioma y evalúa complejidad

2. COMPLIANCE
   - Experto en normativas y regulaciones de cualquier sector e industria
   - Ideal para consultas sobre regulaciones, obligaciones y procesos normativos
   - Puede generar informes relacionados con normas de cumplimiento
   - INCLUYE capacidad de análisis GAP entre políticas internas y normativa aplicable
   - Detecta automáticamente cuando se solicita análisis de brechas o evaluación de políticas

3. REPORT
   - Especializado en generar reportes normativos formales en formato Word
   - Útil cuando el usuario solicita explícitamente un informe o documento 
   - Necesita trabajar con COMPLIANCE para obtener el contenido regulatorio
   - Genera documentos estructurados con secciones estándar (introducción, alcance, análisis, etc.)

#4. WEB_SCRAPING
#   - Especializado en extraer información actualizada de sitios web regulatorios
#   - Útil cuando el usuario solicita información sobre las últimas regulaciones, guidelines o actualizaciones
#   - Usa este agente cuando detectes palabras clave como:
#     * "novedades", "actualizaciones recientes"
#     * "guidelines vigentes", "normativa actual"
#     * Referencias específicas a sitios web regulatorios

Para cada consulta, debes determinar:
1. Si se requiere un análisis previo con QUERY_UNDERSTANDING
2. Si la consulta parece compleja y podría beneficiarse de la descomposición
3. Si el usuario está solicitando un reporte formal (usar REPORT) o solo información (usar COMPLIANCE)
4. Qué agente principal debe responder la consulta

IMPORTANTE para GAP Analysis:
- Si la consulta menciona análisis de brechas, GAP analysis, evaluación de políticas, comparación con normativa, o análisis de cumplimiento de políticas internas, usa COMPLIANCE
- El agente COMPLIANCE detectará automáticamente estos casos y usará las herramientas apropiadas
- NO necesitas crear un agente separado para GAP analysis

Tu respuesta debe ser un plan de orquestación que especifique la secuencia de agentes a utilizar y cualquier información relevante para su ejecución.

Importante:
No respondas directamente la consulta del usuario.
Tu única función es planificar la coordinación entre los agentes especializados.

"""

orchestrator_agent = Agent(
    model=model,
    system_prompt=system_prompt,
    deps_type=OrchestratorDeps,
    output_type=OrchestratorPlan
)

async def execute_orchestration_plan(plan: OrchestratorPlan, query: str, deps: OrchestratorDeps) -> OrchestrationResult:
    """
    Ejecuta un plan de orquestación generado por el orquestador.
    
    Args:
        plan: Plan de orquestación a ejecutar
        query: Consulta original del usuario
        deps: Dependencias necesarias para los agentes
    
    Returns:
        OrchestrationResult: Resultado de la ejecución del plan
    """
    logger.info(f"Ejecutando plan de orquestación - Agente principal: {plan.primary_agent}")
    query_info = None
    effective_query = query
    
    # Preparar dependencias para los diferentes agentes
    query_understanding_deps = QueryUnderstandingDeps(
        supabase=deps.supabase,
        openai_client=deps.openai_client
    )

    report_deps = ReportDeps(
        output_folder="output/reports",
        template_folder="agents/templates",
        openai_client=deps.openai_client
    )

    # Paso 1: Procesar con Query Understanding si el plan lo requiere
    if plan.requires_query_understanding:
        logger.info("Ejecutando paso de comprensión de consulta (Query Understanding)")
        query_info = await process_query_understanding(query, deps=query_understanding_deps)
        
        if query_info.expanded_query:
            effective_query = query_info.expanded_query
            logger.info(f"Usando consulta expandida: {effective_query[:100]}..." if len(effective_query) > 100 else effective_query)
    
    # Paso 2: Manejo de consultas complejas
    if plan.requires_complex_handling and query_info and query_info.decomposed_queries:
        logger.info(f"Procesando consulta compleja con {len(query_info.decomposed_queries)} sub-consultas")
        
        sub_responses = []
        for i, sub_query in enumerate(query_info.decomposed_queries):
            logger.info(f"Procesando sub-consulta {i+1}: {sub_query[:100]}..." if len(sub_query) > 100 else sub_query)
            
            if plan.primary_agent == AgentType.COMPLIANCE:
                # MODIFICACIÓN: Llamar al servicio remoto
                sub_response = await call_expert_service(sub_query, query_info)
                sub_responses.append(sub_response)
        
        # Sintetizar respuestas
        synthesis_prompt = f"Sintetiza de manera coherente las siguientes respuestas a sub-consultas sobre: {query}\n\n"
        for i, sub_response in enumerate(sub_responses):
            synthesis_prompt += f"Respuesta {i+1}:\n{sub_response}\n\n"
        
        completion = await deps.openai_client.chat.completions.create(
            model=llm,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "Eres un experto en normativas encargado de sintetizar múltiples respuestas."},
                {"role": "user", "content": synthesis_prompt}
            ]
        )
        
        synthesized_response = completion.choices[0].message.content
        
        return OrchestrationResult(
            agent_used=plan.primary_agent,
            response=synthesized_response,
            query_info=query_info,
            additional_info={"processed_sub_queries": len(sub_responses)}
        )
    
    # Paso 3: Procesamiento estándar con el agente principal
    logger.info(f"Procesando con el agente principal: {plan.primary_agent}")
    
    if plan.primary_agent == AgentType.COMPLIANCE:
        # MODIFICACIÓN CRÍTICA: Delegar al servicio experto
        response_text = await call_expert_service(effective_query, query_info)
        
        return OrchestrationResult(
            agent_used=plan.primary_agent,
            response=response_text,
            query_info=query_info,
            additional_info={"service": "reasoning_microservice"}
        )

    elif plan.primary_agent == AgentType.REPORT:
        # Primero obtenemos el análisis de compliance del servicio experto
        logger.info("Generando contenido con el agente de compliance para el reporte")
        compliance_response = await call_expert_service(effective_query, query_info)
        
        # Luego generamos el reporte
        logger.info("Generando reporte en formato Word")
        report_result = await process_report_query(
            query=effective_query,
            analysis_data=compliance_response,
            deps=report_deps
        )
        
        report_message = f"""He generado un informe normativo basado en tu consulta.

Título: {report_result.file_path.split('/')[-1].replace('_', ' ').replace('.docx', '')}
Estado: {report_result.message}
Ubicación: {report_result.file_path}

El informe incluye un análisis detallado de las normativas y regulaciones relevantes.
"""
        
        return OrchestrationResult(
            agent_used=plan.primary_agent,
            response=report_message,
            query_info=query_info,
            additional_info={"report_path": report_result.file_path}
        )

    else:
        logger.warning(f"Tipo de agente no implementado: {plan.primary_agent}. Usando compliance.")
        response_text = await call_expert_service(effective_query, query_info)
        
        return OrchestrationResult(
            agent_used=AgentType.COMPLIANCE,
            response=response_text,
            query_info=query_info
        )


# NUEVA FUNCIÓN: Cliente HTTP para el servicio experto
async def call_expert_service(query: str, query_info=None) -> str:
    """
    Llama al servicio experto con razonamiento mediante HTTP.
    
    Args:
        query: Consulta a procesar
        query_info: Información de análisis de consulta (opcional)
    
    Returns:
        str: Respuesta del agente experto
    """
    expert_service_url = os.getenv("EXPERT_SERVICE_URL", "http://localhost:8001")
    
    try:
        logger.info(f"Llamando al servicio experto en {expert_service_url}")
        
        # Preparar payload
        payload = {
            "query": query,
            "query_info": query_info.dict() if query_info else None
        }
        
        # Llamada HTTP con timeout
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{expert_service_url}/expert/query",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("Respuesta recibida del servicio experto")
            return result["response"]
            
    except httpx.TimeoutException:
        logger.error("Timeout al llamar al servicio experto")
        raise Exception("El servicio experto no respondió a tiempo. Por favor, intenta nuevamente.")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP del servicio experto: {e.response.status_code}")
        raise Exception(f"Error al comunicarse con el servicio experto: {e.response.text}")
    except Exception as e:
        logger.error(f"Error inesperado al llamar al servicio experto: {str(e)}")
        raise Exception(f"No se pudo procesar la consulta con el servicio experto: {str(e)}")


async def process_query(query: str, deps: OrchestratorDeps) -> OrchestrationResult:
    """
    Procesa una consulta de usuario a través del sistema multi-agente.
    
    Args:
        query: Consulta del usuario
        deps: Dependencias necesarias para los agentes
    
    Returns:
        OrchestrationResult: Resultado de la ejecución del agente seleccionado
    """
    # Log de la consulta original recibida
    logger.info("=" * 50)
    logger.info(f"ORQUESTADOR: Consulta recibida: {query[:100]}..." if len(query) > 100 else query)
    logger.info("=" * 50)
    
    # El orquestador analiza la consulta y genera un plan de ejecución
    logger.info("ORQUESTADOR: Generando plan de ejecución...")
    orchestration_result = await orchestrator_agent.run(
        query,
        deps=deps
    )
    
    plan = orchestration_result.data
    logger.info(f"ORQUESTADOR: Plan generado - Agente principal: {plan.primary_agent}")
    logger.info(f"ORQUESTADOR: ¿Requiere Query Understanding? {plan.requires_query_understanding}")
    logger.info(f"ORQUESTADOR: ¿Requiere manejo de consulta compleja? {plan.requires_complex_handling}")
    
    if plan.steps:
        for i, step in enumerate(plan.steps):
            logger.info(f"ORQUESTADOR: Paso {i+1}: {step}")
    
    # Ejecutar el plan de orquestación
    logger.info("ORQUESTADOR: Ejecutando plan de orquestación...")
    result = await execute_orchestration_plan(plan, query, deps)
    
    return result


def _convert_regulation_results_to_text(regulation_results):
    """
    Convierte un objeto RegulationResults a texto markdown legible.
    
    Args:
        regulation_results: Objeto RegulationResults del agente de web scraping
        
    Returns:
        str: Texto formateado en markdown
    """
    if not regulation_results:
        return "No se pudo obtener información de regulaciones actualizadas."
    
    # Si el objeto ya es string, devolverlo tal cual
    if isinstance(regulation_results, str):
        return regulation_results
    
    # Si no tiene atributo 'regulations', intentar convertir a string
    if not hasattr(regulation_results, 'regulations'):
        return str(regulation_results)
    
    # Formatear las regulaciones como texto markdown
    response_text = "# Novedades Normativas Encontradas\n\n"
    
    if regulation_results.regulations and len(regulation_results.regulations) > 0:
        for i, regulation in enumerate(regulation_results.regulations, 1):
            response_text += f"## {i}. {regulation.title}\n\n"
            
            if hasattr(regulation, 'reference_number') and regulation.reference_number:
                response_text += f"**Referencia:** {regulation.reference_number}\n\n"
            
            if hasattr(regulation, 'publication_date') and regulation.publication_date:
                response_text += f"**Fecha de publicación:** {regulation.publication_date}\n\n"
            
            if hasattr(regulation, 'document_url') and regulation.document_url:
                response_text += f"**Enlace:** {regulation.document_url}\n\n"
            
            response_text += "---\n\n"
        
        response_text += f"\n*Total de regulaciones encontradas: {len(regulation_results.regulations)}*"
    else:
        response_text += "No se encontraron nuevas regulaciones en el período consultado."
    
    return response_text