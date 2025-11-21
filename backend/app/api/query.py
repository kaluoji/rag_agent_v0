from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime
from app.models.schemas import QueryRequest, QueryResponse
from app.services.agent_service import AgentService, get_agent_service
from app.models.schemas import QueryRequest, QueryResponse, QueryWithDocumentsRequest

# ============================================================================
# NUEVOS IMPORTS PARA MEMORIA
# ============================================================================
from agents.memory_manager import MemoryManager  # ← NUEVO IMPORT

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================================
# MODIFICACIÓN 1: AGREGAR CAMPOS A QueryRequest
# ============================================================================
# Necesitas modificar tu modelo QueryRequest en app/models/schemas.py
# para agregar estos campos opcionales:
#
# class QueryRequest(BaseModel):
#     query: str
#     user_id: str = "default-user"           # ← NUEVO (opcional con default)
#     session_id: Optional[str] = None        # ← NUEVO (opcional)
#     use_memory: bool = True                 # ← NUEVO (opcional, default True)

@router.post("", response_model=QueryResponse)
async def process_query(
    query_request: QueryRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Procesa una consulta normativa y devuelve la respuesta del agente especializado.
    AHORA CON SOPORTE DE MEMORIA CONVERSACIONAL.
    """
    try:
        logger.info(f"Procesando consulta: {query_request.query[:100]}...")
        
        # Generar un ID único para la consulta
        query_id = uuid.uuid4()
        
        # ====================================================================
        # NUEVO: INICIALIZAR MEMORIA SI SE SOLICITA
        # ====================================================================
        session_id = None
        use_memory = getattr(query_request, 'use_memory', True)  # Default True
        
        if use_memory:
            # Obtener user_id y session_id del request (con defaults)
            user_id = getattr(query_request, 'user_id', 'default-user')
            requested_session_id = getattr(query_request, 'session_id', None)
            
            # Inicializar MemoryManager
            memory_manager = agent_service.get_memory_manager()
            
            # Obtener o crear sesión
            session_id = memory_manager.get_or_create_session(
                user_id=user_id,
                session_id=requested_session_id
            )
            
            logger.info(f"💾 Memoria activada - Session ID: {session_id}")
        else:
            logger.info("📭 Memoria desactivada para esta consulta")
        
        # ====================================================================
        # MODIFICACIÓN: Pasar session_id al agent_service
        # ====================================================================
        response, metadata = await agent_service.process_query(
            query_request.query,
            session_id=session_id,      # ← NUEVO PARÁMETRO
            user_id=getattr(query_request, 'user_id', 'default-user')  # ← NUEVO PARÁMETRO
        )
        
        # ====================================================================
        # NUEVO: Agregar session_id a los metadatos de respuesta
        # ====================================================================
        if session_id:
            metadata = metadata or {}
            metadata['session_id'] = session_id
            metadata['has_memory'] = True
        
        # Construir y devolver la respuesta
        query_response = QueryResponse(
            response=response,
            query=query_request.query,
            query_id=query_id,
            timestamp=datetime.now(),
            session_id=session_id,
            metadata=metadata or {}
        )
        
        return query_response
    
    except Exception as e:
        logger.error(f"Error al procesar consulta: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}"
        )

@router.post("/with-documents", response_model=QueryResponse)
async def process_query_with_documents(
    query_request: QueryWithDocumentsRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Procesa una consulta normativa con documentos adjuntos para análisis GAP.
    """
    try:
        logger.info(f"Procesando consulta con documentos: {query_request.query[:100]}...")
        
        # Generar un ID único para la consulta
        query_id = uuid.uuid4()
        
        # ====================================================================
        # NUEVO: INICIALIZAR MEMORIA (igual que en el endpoint anterior)
        # ====================================================================
        session_id = None
        use_memory = getattr(query_request, 'use_memory', True)
        
        if use_memory:
            user_id = getattr(query_request, 'user_id', 'default-user')
            requested_session_id = getattr(query_request, 'session_id', None)
            
            memory_manager = agent_service.get_memory_manager()
            session_id = memory_manager.get_or_create_session(
                user_id=user_id,
                session_id=requested_session_id
            )
            
            logger.info(f"💾 Memoria activada - Session ID: {session_id}")
        
        # Procesar documentos si están presentes
        processed_documents = []
        if query_request.documents:
            for doc in query_request.documents:
                try:
                    # Decodificar el contenido base64
                    import base64
                    decoded_content = base64.b64decode(doc.content).decode('utf-8', errors='ignore')
                    
                    processed_documents.append({
                        "name": doc.name,
                        "type": doc.type,
                        "content": decoded_content,
                        "size": doc.size
                    })
                    
                    logger.info(f"Documento procesado: {doc.name} ({doc.size} bytes)")
                    
                except Exception as e:
                    logger.warning(f"Error procesando documento {doc.name}: {e}")
                    continue
        
        # Enriquecer la consulta con el contenido de los documentos
        enriched_query = query_request.query
        if processed_documents:
            doc = processed_documents[0]
            enriched_query = f"""Realiza un análisis GAP del siguiente documento de política interna.

DOCUMENTO ANALIZAR: {doc['name']}

CONTENIDO DEL DOCUMENTO:
{doc['content'][:20000]}

CONSULTA ESPECÍFICA: {query_request.query}

Por favor, utiliza la herramienta perform_gap_analysis para comparar este documento con la normativa aplicable."""
        
        # ====================================================================
        # MODIFICACIÓN: Pasar session_id al agent_service
        # ====================================================================
        response, metadata = await agent_service.process_query(
            enriched_query,
            session_id=session_id,      # ← NUEVO PARÁMETRO
            user_id=getattr(query_request, 'user_id', 'default-user')  # ← NUEVO PARÁMETRO
        )
        
        # Añadir información sobre documentos procesados a los metadatos
        if processed_documents:
            metadata = metadata or {}
            metadata["processed_documents"] = [
                {"name": doc["name"], "size": doc["size"]} 
                for doc in processed_documents
            ]
        
        # ====================================================================
        # NUEVO: Agregar session_id a los metadatos
        # ====================================================================
        if session_id:
            metadata = metadata or {}
            metadata['session_id'] = session_id
            metadata['has_memory'] = True
        
        # Construir y devolver la respuesta
        query_response = QueryResponse(
            response=response,
            query=query_request.query,
            query_id=query_id,
            timestamp=datetime.now(),
            session_id=session_id,
            metadata=metadata or {}
        )
        
        return query_response
    
    except Exception as e:
        logger.error(f"Error al procesar consulta con documentos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta con documentos: {str(e)}"
        )


# ============================================================================
# NUEVOS ENDPOINTS PARA GESTIÓN DE MEMORIA (OPCIONAL)
# ============================================================================

@router.get("/sessions/{user_id}")
async def get_user_sessions(
    user_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Obtiene las sesiones recientes de un usuario."""
    try:
        memory_manager = agent_service.get_memory_manager()
        sessions = memory_manager.get_user_sessions(user_id, limit=10)
        
        return {
            "user_id": user_id,
            "total_sessions": len(sessions),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                    "metadata": s.metadata
                }
                for s in sessions
            ]
        }
    except Exception as e:
        logger.error(f"Error al obtener sesiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def clear_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Limpia el historial de una sesión."""
    try:
        memory_manager = agent_service.get_memory_manager()
        success = memory_manager.clear_session(session_id)
        
        if success:
            return {"message": f"Sesión {session_id} limpiada exitosamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al limpiar sesión")
    except Exception as e:
        logger.error(f"Error al limpiar sesión: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Obtiene estadísticas de una sesión."""
    try:
        memory_manager = agent_service.get_memory_manager()
        stats = memory_manager.get_session_stats(session_id)
        
        if stats:
            return stats
        else:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))