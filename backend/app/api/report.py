from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Path, Query, Body
from fastapi.responses import FileResponse, HTMLResponse
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import logging
import uuid
import os
import base64
import json
from datetime import datetime
from app.models.schemas import ReportRequest, ReportResponse, AnnotationsRequest, Annotation
from app.services.report_service import ReportService, get_report_service
from app.services.agent_service import AgentService, get_agent_service
from app.core.config import settings
from app.core.websocket import ConnectionManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Importar el singleton directamente
from app.core.websocket import get_connection_manager

# Inicializar el connection_manager
connection_manager = get_connection_manager()

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    agent_service: AgentService = Depends(get_agent_service),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Inicia la generación de un reporte en segundo plano y devuelve un identificador
    para seguir el progreso.
    """
    try:
        # Generar un ID único para el reporte
        report_id = uuid.uuid4()
        
        # Crear la respuesta inicial
        response = ReportResponse(
            report_id=report_id,
            query=report_request.query,
            status="generating",
            timestamp=datetime.now(),
            estimated_time=60,  # Estimar 60 segundos por defecto
            message="Generación de reporte iniciada"
        )
        
        # Iniciar la generación del reporte en segundo plano
        background_tasks.add_task(
            report_service.generate_report,
            query=report_request.query,
            report_id=report_id,
            format=report_request.format,
            agent_service=agent_service,
            connection_manager=connection_manager
        )
        
        logger.info(f"Generación de reporte iniciada. ID: {report_id}")
        return response
    
    except Exception as e:
        logger.error(f"Error al iniciar generación de reporte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al iniciar la generación del reporte: {str(e)}"
        )

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_status(
    report_id: uuid.UUID = Path(...),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Obtiene el estado actual de un reporte en proceso o completado.
    """
    try:
        report_info = await report_service.get_report_info(report_id)
        if not report_info:
            raise HTTPException(
                status_code=404,
                detail=f"Reporte con ID {report_id} no encontrado"
            )
        
        return report_info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener estado del reporte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estado del reporte: {str(e)}"
        )

@router.get("/preview/{report_id}", response_class=HTMLResponse)
async def preview_report(
    report_id: uuid.UUID = Path(...),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Obtiene una vista previa HTML del reporte.
    """
    try:
        html_content = await report_service.get_report_html(report_id)
        if not html_content:
            raise HTTPException(
                status_code=404,
                detail=f"Vista previa del reporte con ID {report_id} no disponible"
            )
        
        return HTMLResponse(content=html_content)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener vista previa del reporte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener vista previa del reporte: {str(e)}"
        )

@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID = Path(...),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Descarga el archivo del reporte en su formato original.
    """
    try:
        report_info = await report_service.get_report_info(report_id)
        if not report_info or not report_info.report_path or report_info.status != "ready":
            raise HTTPException(
                status_code=404,
                detail=f"Reporte con ID {report_id} no disponible para descarga"
            )
        
        file_path = report_info.report_path
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Archivo del reporte no encontrado"
            )
        
        # Obtener el nombre del archivo
        filename = os.path.basename(file_path)
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al descargar el reporte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al descargar el reporte: {str(e)}"
        )

@router.post("/{report_id}/annotations", response_model=List[Annotation])
async def save_annotations(
    annotations_request: AnnotationsRequest,
    report_id: uuid.UUID = Path(...),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Guarda anotaciones asociadas a un reporte.
    """
    try:
        # Verificar que el reporte existe
        report_info = await report_service.get_report_info(report_id)
        if not report_info:
            raise HTTPException(
                status_code=404,
                detail=f"Reporte con ID {report_id} no encontrado"
            )
        
        # Guardar las anotaciones
        saved_annotations = await report_service.save_annotations(
            report_id=report_id,
            annotations=annotations_request.annotations
        )
        
        return saved_annotations
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al guardar anotaciones: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar anotaciones: {str(e)}"
        )

@router.get("/content_by_id/{report_id}")
async def get_report_content_by_id(
    report_id: str = Path(..., description="ID del reporte (formato: 20250426_102841)"),
):
    """
    Obtiene el contenido base64 de un archivo de reporte por su ID.
    """
    try:
        # Construir múltiples patrones de búsqueda
        possible_patterns = [
            f"output/reports/Reporte_Normativo_Regulación_de_Grupos_Económicos_de_Perú_{report_id}.docx",
            f"output/reports/Reporte_Normativo_{report_id}.docx",
            f"output/reports/Reporte_Normativo_*_{report_id}.docx"
        ]
        
        path = None
        
        # Intentar con cada patrón
        for pattern in possible_patterns:
            if '*' in pattern:
                # Usar glob para patrones con wildcard
                import glob
                matching_files = glob.glob(pattern)
                if matching_files:
                    path = matching_files[0]  # Tomar el primer archivo que coincida
                    break
            else:
                # Verificación directa
                if os.path.exists(pattern):
                    path = pattern
                    break
        
        # Si no encontramos nada con los patrones, buscar en todo el directorio
        if not path:
            import glob
            # Buscar cualquier archivo que termine con el report_id
            search_pattern = f"output/reports/*{report_id}.docx"
            matching_files = glob.glob(search_pattern)
            if matching_files:
                path = matching_files[0]
            else:
                # Buscar archivos que contengan el report_id en cualquier parte
                search_pattern = f"output/reports/*{report_id}*.docx"
                matching_files = glob.glob(search_pattern)
                if matching_files:
                    path = matching_files[0]
        
        if not path:
            # Listar archivos disponibles para debugging
            available_files = []
            if os.path.exists("output/reports"):
                available_files = [f for f in os.listdir("output/reports") if f.endswith('.docx')]
            
            raise HTTPException(
                status_code=404,
                detail=f"Archivo no encontrado para el ID: {report_id}. Archivos disponibles: {available_files}"
            )
            
        # Leer el archivo y convertirlo a base64
        with open(path, "rb") as file:
            content = file.read()
            base64_content = base64.b64encode(content).decode("utf-8")
            
        # Obtener el nombre del archivo
        filename = os.path.basename(path)
        
        return {
            "success": True,
            "filename": filename,
            "base64Content": base64_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener contenido del archivo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener contenido del archivo: {str(e)}"
        )

@router.get("/content_by_id/{report_id}/download")
async def download_report_by_id(
    report_id: str = Path(..., description="ID del reporte (formato: 20250426_102841)"),
):
    """
    Descarga un archivo de reporte por su ID.
    """
    try:
        logger.info(f"Descargando archivo para report_id: {report_id}")
        
        # Usar la misma lógica de búsqueda que get_report_content_by_id
        reports_dir = "output/reports"
        if not os.path.exists(reports_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Directorio de reportes no encontrado: {reports_dir}"
            )
        
        # Listar todos los archivos .docx en el directorio
        all_files = [f for f in os.listdir(reports_dir) if f.endswith('.docx')]
        logger.info(f"Archivos .docx disponibles para descarga: {all_files}")
        
        # Buscar archivo que termine con el report_id
        matching_files = [f for f in all_files if f.endswith(f"{report_id}.docx")]
        logger.info(f"Archivos que terminan con {report_id}.docx: {matching_files}")
        
        if not matching_files:
            # Buscar archivo que contenga el report_id
            matching_files = [f for f in all_files if report_id in f]
            logger.info(f"Archivos que contienen {report_id}: {matching_files}")
        
        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail=f"Archivo no encontrado para descarga con ID: {report_id}. Archivos disponibles: {all_files}"
            )
        
        # Tomar el primer archivo que coincida
        filename = matching_files[0]
        file_path = os.path.join(reports_dir, filename)
        
        logger.info(f"Descargando archivo: {file_path}")
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Archivo no encontrado en la ruta: {file_path}"
            )
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al descargar el archivo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al descargar el archivo: {str(e)}"
        )

@router.post("/annotations/{report_id}")
async def save_report_annotations(
    report_id: str = Path(..., description="ID del reporte (formato: 20250426_102841)"),
    request_data: dict = Body(...),
):
    """
    Guarda anotaciones para un documento específico.
    """
    try:
        annotations = request_data.get("annotations", [])
        
        # Validar que el reporte existe
        path = f"output/reports/Reporte_Normativo_{report_id}.docx"
        if not os.path.exists(path):
            raise HTTPException(
                status_code=404,
                detail=f"Documento no encontrado para el ID: {report_id}"
            )
        
        # Guardar las anotaciones en un archivo JSON asociado al documento
        annotations_path = f"output/reports/annotations_{report_id}.json"
        
        with open(annotations_path, "w", encoding="utf-8") as f:
            json.dump(annotations, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": "Anotaciones guardadas correctamente"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al guardar anotaciones: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar anotaciones: {str(e)}"
        )

@router.get("/annotations/{report_id}")
async def get_report_annotations(
    report_id: str = Path(..., description="ID del reporte (formato: 20250426_102841)"),
):
    """
    Obtiene las anotaciones de un documento específico.
    """
    try:
        # Verificar que el archivo de anotaciones existe
        annotations_path = f"output/reports/annotations_{report_id}.json"
        
        if not os.path.exists(annotations_path):
            return {"annotations": []}
        
        # Leer las anotaciones del archivo
        with open(annotations_path, "r", encoding="utf-8") as f:
            annotations = json.load(f)
        
        return {"annotations": annotations}
    
    except Exception as e:
        logger.error(f"Error al obtener anotaciones: {str(e)}")
        return {"annotations": []}

@router.get("/html/{report_id}")
async def get_report_html_endpoint(
    report_id: str = Path(..., description="ID del reporte (UUID o timestamp)"),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Obtiene la previsualización HTML de un reporte.
    Acepta tanto UUID como IDs de timestamp (20251119_014308).
    """
    try:
        from fastapi.responses import JSONResponse
        import glob
        import os
        import uuid as uuid_lib
        
        html_content = None
        
        # Intentar como UUID primero
        try:
            report_uuid = uuid_lib.UUID(report_id)
            html_content = await report_service.get_report_html(report_uuid)
        except ValueError:
            # No es un UUID, buscar por patrón de archivo
            logger.info(f"Buscando reporte por patrón de timestamp: {report_id}")
            
            # Buscar archivo que termine con el report_id
            search_pattern = f"output/reports/*{report_id}.docx"
            matching_files = glob.glob(search_pattern)
            
            if not matching_files:
                # Intentar búsqueda más amplia
                search_pattern = f"output/reports/*{report_id}*.docx"
                matching_files = glob.glob(search_pattern)
            
            if matching_files:
                report_path = matching_files[0]
                logger.info(f"Reporte encontrado: {report_path}")
                html_content = await report_service._generate_html_preview(report_path)
            else:
                logger.warning(f"No se encontró archivo para report_id: {report_id}")
        
        if not html_content:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró previsualización HTML para el reporte {report_id}"
            )
        
        return JSONResponse(content={"html": html_content})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener HTML del reporte {report_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener previsualización: {str(e)}"
        )

@router.websocket("/ws/{report_id}")
async def websocket_report_endpoint(
    websocket: WebSocket,
    report_id: str
):
    """
    WebSocket para actualizaciones en tiempo real de generación de reportes.
    """
    # Obtener el connection_manager global
    global connection_manager
    
    if connection_manager is None:
        logger.error("ConnectionManager no inicializado")
        await websocket.close(code=1011, reason="Service unavailable")
        return
    
    await connection_manager.connect(websocket)
    
    # Agregar al grupo específico del reporte
    group_name = f"report_{report_id}"
    connection_manager.add_to_group(websocket, group_name)
    
    logger.info(f"WebSocket conectado al grupo: {group_name}")
    
    try:
        while True:
            # Mantener la conexión abierta
            data = await websocket.receive_text()
            # Puedes procesar mensajes del cliente si es necesario
            logger.debug(f"Mensaje recibido del cliente: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado del grupo: {group_name}")
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")
        connection_manager.disconnect(websocket)