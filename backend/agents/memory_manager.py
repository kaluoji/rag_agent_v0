# agents/memory_manager.py
"""
Gestor de memoria para sistema multi-agente con Pydantic AI.
Proporciona memoria conversacional (corto plazo) y contextual (largo plazo).
"""

from __future__ import annotations as _annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel
from pydantic_ai import ModelMessage
from pydantic_ai.messages import ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python
from supabase import Client

logger = logging.getLogger(__name__)


class ConversationSession(BaseModel):
    """Representa una sesión de conversación."""
    session_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}


class UserContext(BaseModel):
    """Contexto de largo plazo de un usuario."""
    user_id: str
    preferences: Dict[str, Any] = {}
    domain_knowledge: Dict[str, Any] = {}
    interaction_summary: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MemoryManager:
    """
    Gestor centralizado de memoria para el sistema multi-agente.
    
    Características:
    - Memoria conversacional (corto plazo): Historial de mensajes por sesión
    - Memoria contextual (largo plazo): Preferencias y conocimiento del usuario
    - Persistencia en Supabase
    - Serialización/deserialización automática de mensajes Pydantic AI
    """
    
    def __init__(self, supabase_client: Client):
        """
        Inicializa el gestor de memoria.
        
        Args:
            supabase_client: Cliente de Supabase para persistencia
        """
        self.supabase = supabase_client
        logger.info("MemoryManager inicializado correctamente")
    
    # ========== GESTIÓN DE SESIONES ==========
    
    def create_session(
        self, 
        user_id: str, 
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Crea una nueva sesión de conversación.
        
        Args:
            user_id: ID del usuario
            metadata: Metadatos adicionales de la sesión
            
        Returns:
            session_id: ID único de la sesión creada
        """
        session_id = str(uuid.uuid4())
        
        try:
            self.supabase.table('conversation_sessions').insert({
                'session_id': session_id,
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }).execute()
            
            logger.info(f"✅ Sesión creada: {session_id} para usuario {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Error al crear sesión: {e}")
            raise
    
    def get_or_create_session(
        self, 
        user_id: str, 
        session_id: Optional[str] = None
    ) -> str:
        """
        Obtiene una sesión existente o crea una nueva.
        
        Args:
            user_id: ID del usuario
            session_id: ID de sesión opcional para recuperar
            
        Returns:
            session_id: ID de la sesión (existente o nueva)
        """
        if session_id:
            # Verificar si la sesión existe
            try:
                response = self.supabase.table('conversation_sessions')\
                    .select('session_id')\
                    .eq('session_id', session_id)\
                    .execute()
                
                if response.data:
                    logger.info(f"Sesión existente recuperada: {session_id}")
                    return session_id
                    
            except Exception as e:
                logger.warning(f"Error al buscar sesión existente: {e}")
        
        # Crear nueva sesión
        return self.create_session(user_id)
    
    def get_session_info(self, session_id: str) -> Optional[ConversationSession]:
        """
        Obtiene información de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            ConversationSession o None si no existe
        """
        try:
            response = self.supabase.table('conversation_sessions')\
                .select('*')\
                .eq('session_id', session_id)\
                .execute()
            
            if response.data:
                data = response.data[0]
                return ConversationSession(
                    session_id=data['session_id'],
                    user_id=data['user_id'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at']),
                    metadata=data.get('metadata', {})
                )
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener info de sesión: {e}")
            return None
    
    # ========== GESTIÓN DE MENSAJES (MEMORIA CONVERSACIONAL) ==========
    
    def save_messages(
        self, 
        session_id: str, 
        messages: List[ModelMessage]
    ) -> bool:
        """
        Guarda el historial de mensajes en Supabase.
        
        Args:
            session_id: ID de la sesión
            messages: Lista de mensajes de Pydantic AI
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            # Serializar mensajes usando Pydantic AI
            serialized_messages = to_jsonable_python(messages)
            
            # Guardar en base de datos
            self.supabase.table('conversation_messages').insert({
                'session_id': session_id,
                'message_history': serialized_messages,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            # ✅ NUEVO: Calcular y actualizar contador de tokens
            total_chars = sum(
                len(str(msg.parts)) if hasattr(msg, 'parts') else len(str(msg))
                for msg in messages
            )
            estimated_tokens = total_chars // 4
            
            # Actualizar timestamp y contador de tokens de la sesión
            self.supabase.table('conversation_sessions').update({
                'updated_at': datetime.now().isoformat(),
                'total_tokens': estimated_tokens  # ✅ NUEVO
            }).eq('session_id', session_id).execute()
            
            logger.info(
                f"💾 Guardados {len(messages)} mensajes "
                f"(~{estimated_tokens:,} tokens) para sesión {session_id}"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al guardar mensajes: {e}")
            return False
    
    def load_messages(self, session_id: str, max_tokens: int = 100000) -> List[ModelMessage]:
        """
        Carga el historial de mensajes desde Supabase con límite de tokens.
        
        Args:
            session_id: ID de la sesión
            max_tokens: Número máximo de tokens a cargar (default: 100k)
            
        Returns:
            Lista de ModelMessage (vacía si no hay historial)
        """
        try:
            # Obtener TODOS los registros de mensajes para esta sesión
            response = self.supabase.table('conversation_messages')\
                .select('message_history')\
                .eq('session_id', session_id)\
                .order('created_at', desc=True)\
                .execute()
            
            if not response.data:
                logger.info(f"📭 No hay mensajes previos para sesión {session_id}")
                return []
            
            # Cargar mensajes con límite de tokens
            all_messages = []
            total_tokens = 0
            
            for record in response.data:
                # Deserializar mensajes
                serialized_messages = record['message_history']
                messages = ModelMessagesTypeAdapter.validate_python(serialized_messages)
                
                # Procesar cada mensaje
                for msg in reversed(messages):  # Más antiguos primero
                    # ✅ NUEVO: Filtrar mensajes tipo 'tool' que causan problemas con OpenAI
                    # Solo incluir mensajes de tipo 'user', 'assistant', 'system'
                    if hasattr(msg, 'parts'):
                        # Verificar si alguna parte es de tipo 'tool'
                        has_tool_part = any(
                            hasattr(part, '__class__') and 'Tool' in part.__class__.__name__
                            for part in msg.parts
                        )
                        if has_tool_part:
                            logger.debug(f"🔧 Filtrando mensaje con partes tipo 'tool'")
                            continue
                    
                    # Estimar tokens (1 token ≈ 4 caracteres en inglés/español)
                    msg_content = str(msg.parts) if hasattr(msg, 'parts') else str(msg)
                    msg_tokens = len(msg_content) // 4
                    
                    # Verificar si excede el límite
                    if total_tokens + msg_tokens > max_tokens:
                        logger.warning(
                            f"🔴 Límite de tokens alcanzado: {total_tokens}/{max_tokens}. "
                            f"Cargados {len(all_messages)} mensajes."
                        )
                        return all_messages
                    
                    all_messages.append(msg)
                    total_tokens += msg_tokens
            
            logger.info(
                f"📥 Cargados {len(all_messages)} mensajes "
                f"(~{total_tokens:,} tokens) para sesión {session_id}"
            )
            return all_messages
            
        except Exception as e:
            logger.error(f"❌ Error al cargar mensajes: {e}")
            return []
    
    async def get_or_create_summary(
        self, 
        session_id: str,
        force_refresh: bool = False
    ) -> str:
        """
        Obtiene o genera un resumen de la conversación.
        
        Args:
            session_id: ID de la sesión
            force_refresh: Forzar regeneración del resumen
            
        Returns:
            Resumen de la conversación en texto
        """
        try:
            # Verificar si ya existe un resumen
            if not force_refresh:
                session_info = self.get_session_info(session_id)
                if session_info and session_info.metadata.get('conversation_summary'):
                    logger.info(f"📄 Usando resumen existente para sesión {session_id}")
                    return session_info.metadata['conversation_summary']
            
            # Cargar mensajes para generar resumen
            messages = self.load_messages(session_id, max_tokens=50000)  # Limitar a 50k para resumen
            
            if len(messages) < 4:  # Muy pocos mensajes para resumir
                logger.info(f"⚠️ Muy pocos mensajes para resumir (total: {len(messages)})")
                return ""
            
            # Importar OpenAI (lazy import para no afectar si no se usa)
            from openai import AsyncOpenAI
            import os
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Construir contexto para el resumen
            conversation_text = []
            for msg in messages[-10:]:  # Últimos 10 mensajes
                if hasattr(msg, 'parts'):
                    for part in msg.parts:
                        if hasattr(part, 'content'):
                            role = "Usuario" if hasattr(msg, 'role') and msg.role == 'user' else "Asistente"
                            conversation_text.append(f"{role}: {part.content[:500]}")
            
            context = "\n\n".join(conversation_text)
            
            # Generar resumen con GPT-4o-mini (modelo económico)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un asistente que resume conversaciones sobre temas regulatorios.
                        
Genera un resumen estructurado en 3-5 puntos clave que incluya:
1. Tema principal discutido
2. Normativas o regulaciones mencionadas (ej: GDPR, PSD2, DORA)
3. Preguntas clave del usuario
4. Conclusiones o recomendaciones dadas

Formato: Lista con viñetas, máximo 200 palabras."""
                    },
                    {
                        "role": "user",
                        "content": f"Resume esta conversación:\n\n{context}"
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content
            
            # Guardar resumen en metadata de la sesión
            current_metadata = self.get_session_info(session_id).metadata if self.get_session_info(session_id) else {}
            current_metadata['conversation_summary'] = summary
            current_metadata['summary_generated_at'] = datetime.now().isoformat()
            
            self.supabase.table('conversation_sessions').update({
                'metadata': current_metadata,
                'conversation_summary': summary
            }).eq('session_id', session_id).execute()
            
            logger.info(f"✅ Resumen generado y guardado para sesión {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error al generar resumen: {e}")
            return ""
    
    def update_context_metadata(
        self,
        session_id: str,
        topics: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        regulations: Optional[List[str]] = None,
        key_points: Optional[List[str]] = None
    ) -> bool:
        """
        Actualiza los metadatos contextuales de una sesión.
        
        Args:
            session_id: ID de la sesión
            topics: Lista de temas discutidos
            entities: Lista de entidades mencionadas (empresas, personas, etc.)
            regulations: Lista de regulaciones mencionadas (GDPR, PSD2, etc.)
            key_points: Puntos clave o decisiones tomadas
            
        Returns:
            bool: True si se actualizó exitosamente
        """
        try:
            # Obtener metadata actual
            session_info = self.get_session_info(session_id)
            if not session_info:
                logger.warning(f"⚠️ Sesión {session_id} no encontrada")
                return False
            
            current_metadata = session_info.metadata.get('context_metadata', {})
            
            # Actualizar cada campo si se proporciona (agregando sin duplicar)
            if topics:
                existing_topics = set(current_metadata.get('topics', []))
                existing_topics.update(topics)
                current_metadata['topics'] = list(existing_topics)
            
            if entities:
                existing_entities = set(current_metadata.get('entities', []))
                existing_entities.update(entities)
                current_metadata['entities'] = list(existing_entities)
            
            if regulations:
                existing_regs = set(current_metadata.get('regulations', []))
                existing_regs.update(regulations)
                current_metadata['regulations'] = list(existing_regs)
            
            if key_points:
                existing_points = current_metadata.get('key_points', [])
                existing_points.extend(key_points)
                current_metadata['key_points'] = existing_points[-20:]  # Mantener últimos 20
            
            # Agregar timestamp de última actualización
            current_metadata['last_updated'] = datetime.now().isoformat()
            
            # Guardar en base de datos
            self.supabase.table('conversation_sessions').update({
                'context_metadata': current_metadata
            }).eq('session_id', session_id).execute()
            
            logger.info(f"🏷️ Metadatos actualizados para sesión {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al actualizar metadatos: {e}")
            return False
    
    def clear_session(self, session_id: str) -> bool:
        """
        Limpia los mensajes de una sesión (no elimina la sesión).
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            bool: True si se limpió exitosamente
        """
        try:
            self.supabase.table('conversation_messages')\
                .delete()\
                .eq('session_id', session_id)\
                .execute()
            
            logger.info(f"🗑️ Sesión limpiada: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al limpiar sesión: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Elimina completamente una sesión y sus mensajes.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            # Primero eliminar mensajes
            self.clear_session(session_id)
            
            # Luego eliminar sesión
            self.supabase.table('conversation_sessions')\
                .delete()\
                .eq('session_id', session_id)\
                .execute()
            
            logger.info(f"🗑️ Sesión eliminada completamente: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al eliminar sesión: {e}")
            return False
    
    # ========== GESTIÓN DE CONTEXTO DE USUARIO (MEMORIA A LARGO PLAZO) ==========
    
    def save_user_context(
        self, 
        user_id: str, 
        preferences: Optional[Dict] = None,
        domain_knowledge: Optional[Dict] = None,
        interaction_summary: Optional[str] = None
    ) -> bool:
        """
        Guarda contexto de largo plazo del usuario.
        
        Args:
            user_id: ID del usuario
            preferences: Preferencias del usuario (formato de respuesta, nivel de detalle, etc.)
            domain_knowledge: Conocimiento específico del dominio del usuario
            interaction_summary: Resumen de interacciones previas
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            # Verificar si ya existe contexto
            existing = self.supabase.table('user_context')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            data = {
                'user_id': user_id,
                'preferences': preferences or {},
                'domain_knowledge': domain_knowledge or {},
                'interaction_summary': interaction_summary or '',
                'updated_at': datetime.now().isoformat()
            }
            
            if existing.data:
                # Actualizar contexto existente
                self.supabase.table('user_context')\
                    .update(data)\
                    .eq('user_id', user_id)\
                    .execute()
                logger.info(f"🔄 Contexto actualizado para usuario {user_id}")
            else:
                # Crear nuevo contexto
                data['created_at'] = datetime.now().isoformat()
                self.supabase.table('user_context').insert(data).execute()
                logger.info(f"✅ Contexto creado para usuario {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al guardar contexto de usuario: {e}")
            return False
    
    def load_user_context(self, user_id: str) -> Optional[UserContext]:
        """
        Carga el contexto de largo plazo del usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            UserContext o None si no existe
        """
        try:
            response = self.supabase.table('user_context')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if response.data:
                data = response.data[0]
                return UserContext(
                    user_id=data['user_id'],
                    preferences=data.get('preferences', {}),
                    domain_knowledge=data.get('domain_knowledge', {}),
                    interaction_summary=data.get('interaction_summary', ''),
                    created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
                    updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
                )
            
            logger.info(f"📭 No hay contexto previo para usuario {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error al cargar contexto de usuario: {e}")
            return None
    
    # ========== UTILIDADES Y ESTADÍSTICAS ==========
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Dict con estadísticas (total_messages, user_messages, assistant_messages, etc.)
        """
        try:
            messages = self.load_messages(session_id)
            
            user_count = sum(1 for m in messages if hasattr(m, 'role') and m.role == 'user')
            assistant_count = sum(1 for m in messages if hasattr(m, 'role') and m.role == 'assistant')
            
            # Estimación aproximada de tokens (4 caracteres ≈ 1 token)
            total_chars = sum(len(str(m.content)) for m in messages if hasattr(m, 'content'))
            estimated_tokens = total_chars // 4
            
            return {
                'session_id': session_id,
                'total_messages': len(messages),
                'user_messages': user_count,
                'assistant_messages': assistant_count,
                'estimated_tokens': estimated_tokens,
                'total_characters': total_chars
            }
            
        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas de sesión: {e}")
            return {}
    
    def get_user_sessions(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[ConversationSession]:
        """
        Obtiene las sesiones más recientes de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de sesiones a retornar
            
        Returns:
            Lista de ConversationSession
        """
        try:
            response = self.supabase.table('conversation_sessions')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('updated_at', desc=True)\
                .limit(limit)\
                .execute()
            
            sessions = []
            for data in response.data:
                sessions.append(ConversationSession(
                    session_id=data['session_id'],
                    user_id=data['user_id'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at']),
                    metadata=data.get('metadata', {})
                ))
            
            logger.info(f"📋 Recuperadas {len(sessions)} sesiones para usuario {user_id}")
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Error al obtener sesiones de usuario: {e}")
            return []


# ========== FUNCIÓN DE AYUDA PARA INTEGRACIÓN ==========

def create_memory_manager(supabase_client: Client) -> MemoryManager:
    """
    Factory function para crear un MemoryManager.
    
    Args:
        supabase_client: Cliente de Supabase configurado
        
    Returns:
        MemoryManager: Instancia lista para usar
    """
    return MemoryManager(supabase_client)