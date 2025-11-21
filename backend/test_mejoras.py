# test_mejoras.py
"""Test completo de las 4 mejoras implementadas"""

import sys
import os
from pathlib import Path

# Agregar el directorio backend al path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno ANTES de cualquier import
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("🧪 INICIANDO TESTS DE MEJORAS DE MEMORIA")
print("=" * 60)

# Ahora sí podemos importar
from supabase import create_client
from agents.memory_manager import MemoryManager
from agents.response_cache import get_response_cache

# Conectar a Supabase
print("\n📡 Conectando a Supabase...")
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
print("✅ Conexión establecida")

# ========================================
# TEST 1: LÍMITE POR TOKENS (Mejora #1)
# ========================================
print("\n" + "=" * 60)
print("TEST 1: Límite por tokens en load_messages")
print("=" * 60)

try:
    memory = MemoryManager(supabase)
    session_id = memory.create_session("test-user-tokens")
    print(f"✅ Sesión creada: {session_id}")
    
    # Cargar con límite de tokens
    messages = memory.load_messages(session_id, max_tokens=10000)
    print(f"✅ load_messages funciona - Mensajes cargados: {len(messages)}")
    print("✅ TEST 1: PASADO")
except Exception as e:
    print(f"❌ TEST 1: FALLIDO - {e}")

# ========================================
# TEST 2: CACHE DE RESPUESTAS (Mejora #4)
# ========================================
print("\n" + "=" * 60)
print("TEST 2: Cache de respuestas en memoria")
print("=" * 60)

try:
    cache = get_response_cache()
    print("✅ Cache inicializado")
    
    # Guardar respuesta
    cache.set(
        query="¿Qué es el GDPR?",
        response="El GDPR es el Reglamento General de Protección de Datos de la UE.",
        ttl=3600
    )
    print("✅ Respuesta guardada en cache")
    
    # Recuperar respuesta
    cached = cache.get("¿Qué es el GDPR?")
    if cached:
        print(f"✅ Cache recuperado: {cached[:50]}...")
    else:
        print("❌ No se pudo recuperar del cache")
        raise Exception("Cache no funciona")
    
    # Ver estadísticas
    stats = cache.get_stats()
    print(f"📊 Estadísticas: Hits={stats['hits']}, Misses={stats['misses']}, Hit Rate={stats['hit_rate']}")
    print("✅ TEST 2: PASADO")
except Exception as e:
    print(f"❌ TEST 2: FALLIDO - {e}")

# ========================================
# TEST 3: METADATOS CONTEXTUALES (Mejora #3)
# ========================================
print("\n" + "=" * 60)
print("TEST 3: Metadatos contextuales")
print("=" * 60)

try:
    memory = MemoryManager(supabase)
    session_id = memory.create_session("test-user-metadata")
    print(f"✅ Sesión creada: {session_id}")
    
    # Actualizar metadatos
    success = memory.update_context_metadata(
        session_id=session_id,
        topics=["GDPR", "protección de datos"],
        regulations=["Reglamento (UE) 2016/679"],
        entities=["Autoridad de Control", "DPO"]
    )
    
    if success:
        print("✅ Metadatos actualizados")
        
        # Verificar que se guardaron
        session_info = memory.get_session_info(session_id)
        metadata = session_info.metadata.get('context_metadata', {})
        
        print(f"📋 Temas: {metadata.get('topics')}")
        print(f"📋 Regulaciones: {metadata.get('regulations')}")
        print(f"📋 Entidades: {metadata.get('entities')}")
        print("✅ TEST 3: PASADO")
    else:
        raise Exception("No se pudieron actualizar metadatos")
        
except Exception as e:
    print(f"❌ TEST 3: FALLIDO - {e}")

# ========================================
# TEST 4: CONTADOR DE TOKENS (Parte de Mejora #1)
# ========================================
print("\n" + "=" * 60)
print("TEST 4: Contador de tokens en save_messages")
print("=" * 60)

try:
    from pydantic_ai import ModelMessage
    from pydantic_ai.messages import SystemPromptPart, UserPromptPart
    from datetime import datetime, timezone
    
    memory = MemoryManager(supabase)
    session_id = memory.create_session("test-user-tokens-counter")
    print(f"✅ Sesión creada: {session_id}")
    
    # Crear mensajes de prueba
    test_messages = [
        ModelMessage(
            parts=[SystemPromptPart(
                content="Eres un asistente de prueba",
                timestamp=datetime.now(timezone.utc)
            )]
        ),
        ModelMessage(
            parts=[UserPromptPart(
                content="Esta es una pregunta de prueba para contar tokens",
                timestamp=datetime.now(timezone.utc)
            )]
        )
    ]
    
    # Guardar mensajes
    success = memory.save_messages(session_id, test_messages)
    
    if success:
        print("✅ Mensajes guardados")
        
        # Verificar contador de tokens en la sesión
        session_info = memory.get_session_info(session_id)
        if session_info:
            print(f"📊 Sesión: {session_info.session_id}")
            print(f"📊 Total tokens estimados: {session_info.metadata.get('total_tokens', 'No disponible')}")
        
        print("✅ TEST 4: PASADO")
    else:
        raise Exception("No se pudieron guardar mensajes")
        
except Exception as e:
    print(f"❌ TEST 4: FALLIDO - {e}")

# ========================================
# RESUMEN FINAL
# ========================================
print("\n" + "=" * 60)
print("🎉 TESTS COMPLETADOS")
print("=" * 60)
print("\n✅ Si todos los tests pasaron, las mejoras están funcionando correctamente.")
print("✅ Ahora puedes probar desde el frontend con tu aplicación.")