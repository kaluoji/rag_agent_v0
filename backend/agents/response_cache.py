# agents/response_cache.py
"""
Sistema de cache en memoria para respuestas frecuentes.
Cache simple sin Redis (para entornos sin dependencias externas).
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CachedResponse:
    """Representa una respuesta cacheada."""
    query_hash: str
    response: str
    metadata: Dict[str, Any]
    cached_at: datetime
    ttl_seconds: int
    
    def is_expired(self) -> bool:
        """Verifica si el cache expiró."""
        expiry_time = self.cached_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time


class InMemoryResponseCache:
    """
    Cache en memoria para respuestas de consultas.
    
    Características:
    - Almacenamiento en diccionario Python (sin Redis)
    - TTL configurable por entrada
    - Limpieza automática de entradas expiradas
    - Hash de consultas para matching
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Inicializa el cache.
        
        Args:
            max_size: Número máximo de entradas en cache
            default_ttl: Tiempo de vida por defecto en segundos (default: 1 hora)
        """
        self._cache: Dict[str, CachedResponse] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        logger.info(f"✅ Cache en memoria inicializado (max: {max_size}, TTL: {default_ttl}s)")
    
    def _generate_hash(self, query: str) -> str:
        """
        Genera hash único para una consulta.
        
        Args:
            query: Texto de la consulta
            
        Returns:
            Hash MD5 de la consulta normalizada
        """
        # Normalizar: minúsculas, strip, remover espacios múltiples
        normalized = ' '.join(query.lower().strip().split())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def get(self, query: str) -> Optional[str]:
        """
        Obtiene una respuesta del cache si existe.
        
        Args:
            query: Consulta a buscar
            
        Returns:
            Respuesta cacheada o None si no existe/expiró
        """
        query_hash = self._generate_hash(query)
        
        if query_hash not in self._cache:
            self.misses += 1
            logger.debug(f"❌ Cache miss para query: {query[:50]}...")
            return None
        
        cached = self._cache[query_hash]
        
        # Verificar si expiró
        if cached.is_expired():
            logger.debug(f"⏰ Cache expirado para query: {query[:50]}...")
            del self._cache[query_hash]
            self.misses += 1
            return None
        
        self.hits += 1
        logger.info(f"✅ Cache hit para query: {query[:50]}... (TTL restante: {self._get_ttl_remaining(cached)}s)")
        return cached.response
    
    def set(
        self,
        query: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> None:
        """
        Guarda una respuesta en el cache.
        
        Args:
            query: Consulta original
            response: Respuesta a cachear
            metadata: Metadatos adicionales
            ttl: Tiempo de vida en segundos (usa default si None)
        """
        query_hash = self._generate_hash(query)
        
        # Si el cache está lleno, eliminar la entrada más antigua
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        cached_response = CachedResponse(
            query_hash=query_hash,
            response=response,
            metadata=metadata or {},
            cached_at=datetime.now(),
            ttl_seconds=ttl or self.default_ttl
        )
        
        self._cache[query_hash] = cached_response
        logger.info(f"💾 Respuesta cacheada para query: {query[:50]}... (TTL: {cached_response.ttl_seconds}s)")
    
    def clear(self) -> None:
        """Limpia todo el cache."""
        count = len(self._cache)
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info(f"🗑️ Cache limpiado ({count} entradas eliminadas)")
    
    def cleanup_expired(self) -> int:
        """
        Elimina entradas expiradas del cache.
        
        Returns:
            Número de entradas eliminadas
        """
        expired_keys = [
            key for key, cached in self._cache.items()
            if cached.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"🧹 Limpieza de cache: {len(expired_keys)} entradas expiradas eliminadas")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Diccionario con estadísticas
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate': f"{hit_rate:.2f}%",
            'default_ttl': self.default_ttl
        }
    
    def _evict_oldest(self) -> None:
        """Elimina la entrada más antigua del cache."""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].cached_at
        )
        
        logger.debug(f"🗑️ Evicting oldest cache entry: {oldest_key}")
        del self._cache[oldest_key]
    
    def _get_ttl_remaining(self, cached: CachedResponse) -> int:
        """Calcula el TTL restante en segundos."""
        expiry_time = cached.cached_at + timedelta(seconds=cached.ttl_seconds)
        remaining = (expiry_time - datetime.now()).total_seconds()
        return max(0, int(remaining))


# ========== INSTANCIA GLOBAL DEL CACHE ==========

_global_cache: Optional[InMemoryResponseCache] = None


def get_response_cache() -> InMemoryResponseCache:
    """
    Obtiene la instancia global del cache (singleton).
    
    Returns:
        Instancia del cache
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = InMemoryResponseCache(
            max_size=1000,  # Configurar según necesidades
            default_ttl=3600  # 1 hora por defecto
        )
    
    return _global_cache