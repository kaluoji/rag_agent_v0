from __future__ import annotations as _annotations

import logging
import json
import httpx
import os
from enum import Enum
from typing import List, Dict, Optional, Union, Any, Literal
from pydantic_ai import ModelMessage 

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from supabase import Client

from app.core.config import settings
from agents.ai_expert_v1 import ai_expert, AIDeps, debug_run_agent
from agents.understanding_query import process_query as process_query_understanding, QueryUnderstandingDeps, QueryInfo
from agents.report_agent import report_agent, ReportDeps, process_report_query
from agents.memory_manager import MemoryManager 
#from agents.web_scraping_agent import web_scraping_agent, WebScrapingDeps
#from agents.risk_assessment_agent import risk_assessment_agent, RiskAssessmentDeps
#from agents.normative_report_agent import normative_report_agent, ReportDeps as NormativeReportDeps, process_report_query

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Inicialización del modelo
llm = settings.llm_model
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

model = OpenAIModel(llm)

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
    memory_manager: Optional[MemoryManager] = None  # ← NUEVO
    session_id: Optional[str] = None                # ← NUEVO
    user_id: Optional[str] = None                   # ← NUEVO

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
   - INCLUYE capacidad de análisis GAP entre políticas internas y normativa aplicable
   - Detecta automáticamente cuando se solicita análisis de brechas o evaluación de políticas

3. REPORT
   - Especializado en generar reportes normativos formales en formato Word
   - Útil cuando el usuario solicita explícitamente un informe o documento 
   - Necesita trabajar con COMPLIANCE para obtener el contenido regulatorio
   - Genera documentos estructurados con secciones estándar (introducción, alcance, análisis, etc.)

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

async def execute_orchestration_plan(plan: OrchestratorPlan, query: str, deps: OrchestratorDeps, message_history: Optional[List[ModelMessage]] = None) -> OrchestrationResult:
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
    ai_deps = AIDeps(
        supabase=deps.supabase,
        openai_client=deps.openai_client,
        memory_manager=deps.memory_manager,  # ← NUEVO
        session_id=deps.session_id            # ← NUEVO
    )
    
    query_understanding_deps = QueryUnderstandingDeps(
        supabase=deps.supabase,
        openai_client=deps.openai_client
    )

    report_deps = ReportDeps(
        output_folder="output/reports",
        template_folder="agents/templates",
        openai_client=deps.openai_client
    )

    print(f"Directorio actual: {os.getcwd()}")
    print(f"¿Existe agents/templates/?: {os.path.exists('agents/templates')}")
    print(f"¿Existe el template?: {os.path.exists('agents/templates/Template_Regulatory_Report_AgentIA_v0.docx')}")
    if os.path.exists('agents/templates'):
        print(f"Archivos en agents/templates/: {os.listdir('agents/templates')}")

    # Paso 1: Procesar con Query Understanding si el plan lo requiere
    if plan.requires_query_understanding:
        logger.info("Ejecutando paso de comprensión de consulta (Query Understanding)")
        query_info = await process_query_understanding(query, deps=query_understanding_deps)
        
        # Si tenemos una consulta expandida, la usamos
        if query_info.expanded_query:
            effective_query = query_info.expanded_query
            logger.info(f"Usando consulta expandida: {effective_query[:100]}..." if len(effective_query) > 100 else effective_query)
    
    # Paso 2: Si la consulta es compleja y tenemos información de Query Understanding, 
    # procesamos cada sub-consulta
    if plan.requires_complex_handling and query_info and query_info.decomposed_queries:
        logger.info(f"Procesando consulta compleja con {len(query_info.decomposed_queries)} sub-consultas")
        
        # Procesar cada sub-consulta
        sub_responses = []
        for i, sub_query in enumerate(query_info.decomposed_queries):
            logger.info(f"Procesando sub-consulta {i+1}: {sub_query[:100]}..." if len(sub_query) > 100 else sub_query)
            
            if plan.primary_agent == AgentType.COMPLIANCE:
                sub_response = await debug_run_agent(sub_query, deps=ai_deps)
                sub_responses.append(sub_response.output)
        
        # Sintetizar los resultados de las sub-consultas
        synthesis_prompt = f"Sintetiza de manera coherente las siguientes respuestas a sub-consultas sobre: {query}\n\n"
        for i, sub_response in enumerate(sub_responses):
            synthesis_prompt += f"Respuesta {i+1} (a la sub-consulta: {query_info.decomposed_queries[i]}):\n{sub_response}\n\n"
        
        # Usar el modelo para sintetizar una respuesta coherente
        completion = await deps.openai_client.chat.completions.create(
            model=llm,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "Eres un experto en normativas y regulaciones de cualquier sector e industria encargado de sintetizar múltiples respuestas en una única respuesta coherente y completa. Conserva toda la información relevante, elimina redundancias y organiza el contenido de manera lógica."},
                {"role": "user", "content": synthesis_prompt}
            ]
        )
        
        synthesized_response = completion.choices[0].message.content
        
        # Devolver la respuesta sintetizada
        return OrchestrationResult(
            agent_used=plan.primary_agent,
            response=synthesized_response,
            query_info=query_info,
            additional_info={"processed_sub_queries": len(sub_responses)}
        )
    
    # Paso 3: Procesamiento estándar con el agente principal
    logger.info(f"Procesando con el agente principal: {plan.primary_agent}")
    
    if plan.primary_agent == AgentType.COMPLIANCE:
        response = await debug_run_agent(effective_query, deps=ai_deps, query_info=query_info, message_history=message_history)
        
        if deps.memory_manager and deps.session_id:
            all_messages = response.all_messages()
            deps.memory_manager.save_messages(deps.session_id, all_messages)


        return OrchestrationResult(
            agent_used=plan.primary_agent,
            response=response.output,
            query_info=query_info,
            additional_info={"usage": response.usage()}
        )

    elif plan.primary_agent == AgentType.REPORT:
        # Primero obtenemos el análisis de compliance
        logger.info("Generando contenido con el agente de compliance para el reporte")
        compliance_response = await debug_run_agent(effective_query, deps=ai_deps, query_info=query_info)
        
        # Luego generamos el reporte con ese contenido
        logger.info("Generando reporte en formato Word con el contenido de compliance")
        report_result = await process_report_query(
            query=effective_query,
            analysis_data=compliance_response.output,
            deps=report_deps
        )
        
        # Preparar respuesta apropiada
        report_message = f"""He generado un informe normativo basado en tu consulta.

Título: {report_result.file_path.split('/')[-1].replace('_', ' ').replace('.docx', '')}
Estado: {report_result.message}
Ubicación: {report_result.file_path}

El informe incluye un análisis detallado de las normativas y regulaciones relevantes, conclusiones y recomendaciones.
"""
        
        return OrchestrationResult(
            agent_used=plan.primary_agent,
            response=report_message,
            query_info=query_info,
            additional_info={"report_path": report_result.file_path}
        )

#    elif plan.primary_agent == AgentType.WEB_SCRAPING:
#        logger.info("Procesando con el agente de web scraping")
        
        # Crear dependencias asíncronas
#        async with httpx.AsyncClient() as async_client:
#            web_scraping_deps = WebScrapingDeps(
#                http_client=async_client
#            )
            
            # Usar la versión asíncrona del agente
#            try:
#                response = await web_scraping_agent.run(
#                    effective_query, 
#                    deps=web_scraping_deps
#                )
                
                # Convertir RegulationResults a string legible
#                response_text = _convert_regulation_results_to_text(response.output)
                
#                return OrchestrationResult(
#                    agent_used=plan.primary_agent,
#                    response=response_text,  # ← Ahora devolvemos string en lugar del objeto
#                    query_info=query_info,
#                    additional_info={"usage": response.usage()}
#                )
#            except Exception as e:
#                logger.error(f"Error en web scraping agent: {e}")
                # Fallback al agente de compliance
#                response = await debug_run_agent(effective_query, deps=ai_deps)
#                return OrchestrationResult(
#                    agent_used=AgentType.COMPLIANCE,
#                    response=response.output,
#                    query_info=query_info,
#                    additional_info={"fallback_used": True, "original_error": str(e)}
#                )

    else:
        # Si no se reconoce el tipo de agente, usamos el agente de compliance por defecto
        logger.warning(f"Tipo de agente principal no implementado: {plan.primary_agent}. Usando agente de compliance por defecto.")
        response = await debug_run_agent(effective_query, deps=ai_deps, query_info=query_info, message_history=message_history)
        
        if deps.memory_manager and deps.session_id:
            all_messages = response.all_messages()
            deps.memory_manager.save_messages(deps.session_id, all_messages)
            logger.info(f"💾 Mensajes guardados en sesión {deps.session_id}")


        return OrchestrationResult(
            agent_used=AgentType.COMPLIANCE,
            response=response.output,
            query_info=query_info,
            additional_info={"usage": response.usage()}
        )

async def process_query(query: str, deps: OrchestratorDeps, message_history: Optional[List[ModelMessage]] = None ) -> OrchestrationResult:
    """
    Procesa una consulta de usuario a través del sistema multi-agente.
    
    Args:
        query: Consulta del usuario
        deps: Dependencias necesarias para los agentes
    
    Returns:
        OrchestrationResult: Resultado de la ejecución del agente seleccionado
    """
    if deps.memory_manager and deps.session_id and message_history is None:
        message_history = deps.memory_manager.load_messages(deps.session_id)
        logger.info(f"📥 Historial cargado: {len(message_history)} mensajes")

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
    
    plan = orchestration_result.output
    logger.info(f"ORQUESTADOR: Plan generado - Agente principal: {plan.primary_agent}")
    logger.info(f"ORQUESTADOR: ¿Requiere Query Understanding? {plan.requires_query_understanding}")
    logger.info(f"ORQUESTADOR: ¿Requiere manejo de consulta compleja? {plan.requires_complex_handling}")
    
    if plan.steps:
        for i, step in enumerate(plan.steps):
            logger.info(f"ORQUESTADOR: Paso {i+1}: {step}")
    
    # Ejecutar el plan de orquestación
    logger.info("ORQUESTADOR: Ejecutando plan de orquestación...")
    result = await execute_orchestration_plan(plan, query, deps, message_history)
    
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