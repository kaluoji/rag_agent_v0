# agents/report_agent.py - Versión corregida
from __future__ import annotations as _annotations

import os
import datetime
import logging
import re
from typing import Optional, Dict, Any, List

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.core.config import settings

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización del modelo
llm = settings.llm_model
model = OpenAIModel(llm)

class ReportDeps(BaseModel):
    output_folder: str = "output/reports"
    template_folder: str = "agents/templates"
    openai_client: AsyncOpenAI

    class Config:
        arbitrary_types_allowed = True

class ReportResult(BaseModel):
    file_path: str
    report_type: str = "word"
    message: str = "Reporte generado exitosamente"
    sections_filled: List[str] = []

# Mapeo de placeholders del template
TEMPLATE_PLACEHOLDERS = {
    "{{EXECUTIVE_SUMMARY}}": "executive_summary",
    "{{ALCANCE}}": "scope", 
    "{{FINDINGS}}": "findings",
    "{{CONCLUSIONES_RECOMENDACIONES}}": "conclusions_recommendations",

}

report_system_prompt = """
Eres un experto en análisis regulatorio que genera reportes profesionales diferenciados por sección.

PRINCIPIOS CLAVE:
1. DIFERENCIACIÓN: Cada sección debe tener un propósito único y contenido específico
2. PROGRESIÓN: Las secciones deben complementarse, no repetirse
3. ESPECIFICIDAD: Usar solo información concreta de la base de conocimiento
4. ACCIONABILIDAD: Las recomendaciones deben ser implementables

FLUJO LÓGICO:
- Executive Summary: Vista de alto nivel (QUÉ)
- Alcance: Perímetro del análisis (DÓNDE y CUÁNDO)  
- Findings: Hallazgos específicos (QUÉ se encontró)
- Conclusiones: Interpretación y acciones (QUÉ hacer)

PROHIBIDO:
- Repetir la misma información en múltiples secciones
- Inventar artículos o disposiciones no documentadas
- Usar lenguaje genérico sin base en la documentación
- Generar recomendaciones sin fundamento específico

Template fijo: "Template_Regulatory_Report_AgentIA.docx"
"""

report_agent = Agent(
    model=model,
    system_prompt=report_system_prompt,
    deps_type=ReportDeps,
    output_type=ReportResult,
    retries=2
)

def find_placeholders_in_document(doc_path: str) -> List[str]:
    """
    Encuentra todos los placeholders en un documento Word.
    """
    doc = Document(doc_path)
    placeholders = []
    
    # Buscar en párrafos
    for paragraph in doc.paragraphs:
        text = paragraph.text
        # Buscar patrones que empiecen con {{ y terminen con }}
        found = re.findall(r'\{\{[^}]+\}\}', text)
        placeholders.extend(found)
    
    # Buscar en tablas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    text = paragraph.text
                    found = re.findall(r'\{\{[^}]+\}\}', text)
                    placeholders.extend(found)
    
    logger.info(f"Placeholders encontrados en el documento: {placeholders}")
    return list(set(placeholders))

def replace_placeholder_in_document(doc: Document, placeholder: str, content: str):
    """
    Reemplaza un placeholder específico en todo el documento con el contenido generado.
    """
    replacements_made = 0
    
    # Reemplazar en párrafos
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            # Reemplazar el texto completo del párrafo
            new_text = paragraph.text.replace(placeholder, content)
            paragraph.clear()
            paragraph.add_run(new_text)
            replacements_made += 1
    
    # Reemplazar en tablas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if placeholder in paragraph.text:
                        new_text = paragraph.text.replace(placeholder, content)
                        paragraph.clear()
                        paragraph.add_run(new_text)
                        replacements_made += 1
    
    logger.info(f"Realizados {replacements_made} reemplazos para el placeholder '{placeholder}'")

@report_agent.tool
async def generate_report_from_template(
    ctx: RunContext[ReportDeps], 
    analysis_data: str, 
    template_name: str = "Template_Regulatory_Report_AgentIA.docx",
    regulation_name: str = "Normativa Analizada",
    output_filename: str = None
) -> ReportResult:
    """
    Genera un reporte usando un template de Word existente.
    """
    try:
        # Construir rutas
        template_path = os.path.join(ctx.deps.template_folder, template_name)
        
        if not os.path.exists(template_path):
            logger.error(f"Template no encontrado en: {template_path}")
            # Listar archivos disponibles para debugging
            if os.path.exists(ctx.deps.template_folder):
                available_files = os.listdir(ctx.deps.template_folder)
                logger.info(f"Archivos disponibles en template_folder: {available_files}")
            raise FileNotFoundError(f"Template no encontrado: {template_path}")
        
        # Cargar el template
        doc = Document(template_path)
        logger.info(f"Template cargado exitosamente desde: {template_path}")
        
        # Encontrar placeholders en el documento
        placeholders = find_placeholders_in_document(template_path)
        logger.info(f"Placeholders encontrados: {placeholders}")
        
        if not placeholders:
            logger.warning("No se encontraron placeholders en el documento template")
        
        # Reemplazar fecha y nombre de regulación
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        replace_placeholder_in_document(doc, "[Fecha]", current_date)
        replace_placeholder_in_document(doc, "[Ley analizada]", regulation_name)
        
        # Generar contenido para cada sección
        sections_filled = []
        
        for placeholder in placeholders:
            logger.info(f"Procesando placeholder: {placeholder}")
            
            # Buscar el placeholder en nuestro mapeo
            section_key = None
            for mapped_placeholder, key in TEMPLATE_PLACEHOLDERS.items():
                if placeholder.strip() == mapped_placeholder.strip():
                    section_key = key
                    break
            
            if section_key:
                logger.info(f"Generando contenido para sección: {section_key}")
                content = await generate_section_content(
                    ctx.deps.openai_client, 
                    section_key, 
                    analysis_data, 
                    regulation_name
                )
                
                replace_placeholder_in_document(doc, placeholder, content)
                sections_filled.append(section_key)
                logger.info(f"Sección completada: {section_key}")
            else:
                logger.warning(f"Placeholder no reconocido: {placeholder}")
        
        # Crear directorio de salida si no existe
        if not os.path.exists(ctx.deps.output_folder):
            os.makedirs(ctx.deps.output_folder)
            logger.info(f"Directorio creado: {ctx.deps.output_folder}")
        
        # Generar nombre de archivo
        if output_filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_regulation_name = re.sub(r'[^\w\s-]', '', regulation_name).strip()
            safe_regulation_name = re.sub(r'[-\s]+', '_', safe_regulation_name)
            output_filename = f"Reporte_Normativo_{safe_regulation_name}_{timestamp}.docx"
        
        output_path = os.path.join(ctx.deps.output_folder, output_filename)
        doc.save(output_path)
        
        logger.info(f"Reporte generado exitosamente: {output_path}")
        
        return ReportResult(
            file_path=output_path,
            report_type="word",
            message=f"Reporte generado usando template {template_name}. Secciones completadas: {len(sections_filled)}",
            sections_filled=sections_filled
        )
        
    except Exception as e:
        logger.error(f"Error generando reporte desde template: {e}")
        raise e

# En agents/report_agent.py, reemplaza la función generate_section_content completa:
async def generate_section_content(
    openai_client: AsyncOpenAI, 
    section_key: str, 
    analysis_data: str, 
    regulation_name: str
) -> str:
    """
    Genera contenido específico para una sección del reporte usando EXCLUSIVAMENTE
    la información ya recuperada de Supabase por el agente de compliance.
    """
    
    # MEJORA: Analizar si analysis_data contiene información de Supabase
    has_supabase_data = "Content:" in analysis_data or "title" in analysis_data.lower() or "artículo" in analysis_data.lower()
    
    section_prompts = {
    "executive_summary": f"""
INFORMACIÓN DE LA BASE DE CONOCIMIENTO:
{analysis_data}

TAREA: Genera un EXECUTIVE SUMMARY de MÁXIMO 150 palabras para {regulation_name}.

ESTRUCTURA OBLIGATORIA:
- Párrafo 1 (40 palabras): Propósito principal de la regulación
- Párrafo 2 (60 palabras): 3 hallazgos más críticos (solo los MÁS importantes)
- Párrafo 3 (50 palabras): Impacto operacional clave y conclusión ejecutiva

REGLAS ESTRICTAS:
- Usar SOLO los 3 artículos/obligaciones MÁS críticos identificados
- Eliminar frases de transición innecesarias
- Lenguaje directo y cuantificable cuando sea posible
- NO duplicar información que aparecerá en Findings detallados
""",

    "scope": f"""
INFORMACIÓN DE LA BASE DE CONOCIMIENTO:
{analysis_data}

TAREA: Define el ALCANCE específico del análisis para {regulation_name}.

ESTRUCTURA:
1. Normativas y artículos ESPECÍFICOS analizados (enumera cuáles)
2. Áreas organizacionales afectadas según la documentación
3. Período temporal cubierto por el análisis
4. Limitaciones del análisis (qué NO se incluye)
5. Metodología de revisión utilizada

REGLAS:
- Ser específico sobre QUÉ se analizó y QUÉ NO
- Mencionar fechas, versiones de documentos si están disponibles
- Clarificar el perímetro exacto del análisis
- No repetir conclusiones (eso va en otra sección)
""",

    "findings": f"""
INFORMACIÓN DE LA BASE DE CONOCIMIENTO:
{analysis_data}

TAREA: Desarrolla FINDINGS categorizados por CRITICIDAD para {regulation_name}.

ESTRUCTURA OBLIGATORIA:

**CRÍTICOS (Impacto Alto/Inmediato):**
- [Artículo X]: [Obligación específica] - Impacto: [Descripción concreta] - Plazo: [Si aplica]

**IMPORTANTES (Impacto Medio/Seguimiento):**
- [Artículo Y]: [Requisito específico] - Implicación: [Qué significa para la empresa]

**INFORMATIVOS (Conocimiento General):**
- [Artículo Z]: [Definición/Criterio] - Relevancia: [Por qué es importante conocerlo]

**BRECHAS IDENTIFICADAS:**
- Información faltante en la documentación analizada
- Aspectos que requieren clarificación adicional

REGLAS:
- Máximo 2 hallazgos por categoría (total 8 hallazgos)
- Cada hallazgo debe incluir: Artículo + Obligación + Impacto concreto
- Usar términos cuantificables: "15 días", "4%", "dos veces al año"
- Evitar generalidades, ser específico en las implicaciones
""",

    "conclusions_recommendations": f"""
INFORMACIÓN DE LA BASE DE CONOCIMIENTO:
{analysis_data}

TAREA: Genera RECOMENDACIONES ACCIONABLES para {regulation_name}.

ESTRUCTURA OBLIGATORIA:

**ACCIONES INMEDIATAS (0-30 días):**
1. [Acción específica] - Responsable sugerido: [Área] - Entregable: [Qué producir]
2. [Acción específica] - Responsable sugerido: [Área] - Entregable: [Qué producir]

**IMPLEMENTACIÓN MEDIANO PLAZO (1-6 meses):**
1. [Proyecto específico] - Recursos estimados: [Tiempo/Personal] - Resultado esperado: [Métrica]
2. [Mejora de proceso] - Inversión requerida: [Estimación] - Beneficio: [Reducción de riesgo]

**MONITOREO CONTINUO:**
1. [KPI específico a monitorear] - Frecuencia: [Mensual/Trimestral] - Responsable: [Área]
2. [Control a implementar] - Automatización: [Sí/No] - Alerta: [Criterio]

REGLAS CRÍTICAS:
- Cada recomendación debe estar vinculada a un artículo/hallazgo específico
- Incluir estimaciones realistas de recursos y tiempo
- Definir entregables concretos, no conceptos vagos
- Priorizar por impacto regulatorio (sanción potencial) vs esfuerzo de implementación
"""
}
    
    prompt = section_prompts.get(section_key, f"Genera contenido para la sección {section_key} basado EXCLUSIVAMENTE en: {analysis_data}")
    
    try:
        completion = await openai_client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.0,  # Temperatura baja para ser más fiel a los datos
            max_tokens=5000,
            messages=[
                {
                    "role": "system", 
                    "content": """Eres un experto en análisis regulatorio que trabaja EXCLUSIVAMENTE con información específica de bases de conocimiento.

INSTRUCCIONES CRÍTICAS:
1. USA SOLO la información proporcionada en el contexto
2. NO agregues conocimiento general o información externa
3. Cita específicamente artículos, secciones y disposiciones encontradas
4. Si la información es limitada, sé transparente sobre las limitaciones
5. Genera SOLO texto plano sin formato Markdown
6. Mantén fidelidad absoluta a la documentación proporcionada
7. Estructura el contenido de forma profesional y coherente

PROHIBIDO:
- Inventar artículos o disposiciones no mencionadas
- Agregar información de conocimiento general
- Usar formato Markdown (**, #, -, etc.)
- Hacer suposiciones no respaldadas por la documentación"""
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        content = completion.choices[0].message.content.strip()
        
        # Limpiar cualquier formato Markdown
        content = content.replace("**", "")
        content = content.replace("*", "")
        content = content.replace("###", "")
        content = content.replace("##", "")
        content = content.replace("#", "")
        content = re.sub(r'\n\s*-\s+', '\n\n', content)
        content = re.sub(r'\n\s*\*\s+', '\n\n', content)
        
        # VERIFICACIÓN: Asegurar que se está usando información de Supabase
        if has_supabase_data:
            logger.info(f"Sección {section_key} generada usando información de Supabase")
        else:
            logger.warning(f"Sección {section_key} generada con información limitada - verificar recuperación de Supabase")
        
        return content
        
    except Exception as e:
        logger.error(f"Error generando contenido para sección {section_key}: {e}")
        return f"[Error generando contenido para {section_key}]"

# Función principal para procesar consultas con template - CORREGIDA
async def process_report_query(
    query: str, 
    analysis_data: str, 
    deps: ReportDeps,
    template_name: str = "Template_Regulatory_Report_AgentIA.docx",
    regulation_name: str = None
) -> ReportResult:
    """
    Procesa una consulta para generar un reporte usando un template específico.
    """
    logger.info(f"Procesando consulta con template: {query[:100]}...")
    
    # Extraer nombre de regulación si no se proporciona
    if regulation_name is None:
        try:
            completion = await deps.openai_client.chat.completions.create(
                model=settings.llm_model,
                temperature=0.0,
                messages=[
                    {
                        "role": "system", 
                        "content": "Extrae el nombre de la regulación o ley mencionada en la consulta. Responde solo con el nombre."
                    },
                    {"role": "user", "content": query}
                ]
            )
            regulation_name = completion.choices[0].message.content.strip()
        except:
            regulation_name = "Regulación Analizada"
    
    # CORRECCIÓN: Crear un RunContext simulado usando los datos necesarios
    try:
        # Llamar directamente a la función generate_report_from_template
        # creando un contexto simulado
        class MockRunContext:
            def __init__(self, deps):
                self.deps = deps
        
        mock_ctx = MockRunContext(deps)
        
        return await generate_report_from_template(
            mock_ctx,
            analysis_data=analysis_data,
            template_name=template_name,
            regulation_name=regulation_name
        )
        
    except Exception as e:
        logger.error(f"Error procesando consulta con template: {e}")
        return ReportResult(
            file_path="",
            message=f"Error generando reporte con template: {str(e)}"
        )