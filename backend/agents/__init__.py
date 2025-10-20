# Este archivo permite la importación de agentes desde el paquete agents

# Importamos y exponemos los agentes disponibles
from agents.ai_expert_v1 import ai_expert, AIDeps
from agents.report_agent import report_agent, ReportDeps
from agents.orchestrator_agent import orchestrator_agent, OrchestratorDeps, process_query, AgentType, OrchestrationResult


# Exportamos los nombres para facilitar las importaciones
__all__ = [
    'ai_expert', 
    'AIDeps',
    'report_agent', 
    'ReportDeps',
    'orchestrator_agent',
    'OrchestratorDeps',
    'process_query',
    'AgentType',
    'OrchestrationResult',
    'regulatory_scraper',
    'ScraperDeps',
    'ScrapingResult',
    'Publication'
]