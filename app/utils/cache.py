import redis
import json
import pickle
from typing import Any, Optional, Union
from functools import wraps
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Gestor de caché con Redis como backend"""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Conectar a Redis con manejo de errores"""
        try:
            # Configuración básica de Redis
            self.redis_client = redis.Redis(
                host=getattr(settings, 'redis_host', 'localhost'),
                port=getattr(settings, 'redis_port', 6379),
                db=getattr(settings, 'redis_db', 0),
                decode_responses=False,  # Para manejar datos binarios
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Probar la conexión
            self.redis_client.ping()
            logger.info("Conexión a Redis establecida exitosamente")
        except Exception as e:
            logger.warning(f"No se pudo conectar a Redis: {e}. Caché deshabilitado.")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Verificar si Redis está disponible"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Guardar valor en caché
        
        Args:
            key: Clave del caché
            value: Valor a guardar
            expire: Tiempo de expiración en segundos (default: 5 minutos)
        """
        if not self.is_available():
            return False
        
        try:
            # Serializar el valor
            serialized_value = pickle.dumps(value)
            self.redis_client.setex(key, expire, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error al guardar en caché {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del caché"""
        if not self.is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return pickle.loads(value)
        except Exception as e:
            logger.error(f"Error al obtener del caché {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Eliminar clave del caché"""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error al eliminar del caché {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Eliminar claves que coincidan con un patrón"""
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error al eliminar patrón del caché {pattern}: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Limpiar todo el caché"""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error al limpiar caché: {e}")
            return False

# Instancia global del gestor de caché
cache_manager = CacheManager()

def cache_key(*args, **kwargs) -> str:
    """Generar clave de caché a partir de argumentos"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)

def cached(expire: int = 300, key_prefix: str = ""):
    """Decorador para cachear resultados de funciones
    
    Args:
        expire: Tiempo de expiración en segundos
        key_prefix: Prefijo para la clave de caché
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de caché
            func_name = f"{func.__module__}.{func.__name__}"
            cache_key_str = cache_key(key_prefix, func_name, *args, **kwargs)
            
            # Intentar obtener del caché
            cached_result = cache_manager.get(cache_key_str)
            if cached_result is not None:
                logger.debug(f"Cache hit para {cache_key_str}")
                return cached_result
            
            # Ejecutar función y guardar resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key_str, result, expire)
            logger.debug(f"Cache miss para {cache_key_str}, resultado guardado")
            
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str):
    """Invalidar caché por patrón"""
    return cache_manager.delete_pattern(pattern)

def get_cache_stats() -> dict:
    """Obtener estadísticas del caché"""
    if not cache_manager.is_available():
        return {"available": False, "error": "Redis no disponible"}
    
    try:
        info = cache_manager.redis_client.info()
        return {
            "available": True,
            "used_memory": info.get('used_memory_human', 'N/A'),
            "connected_clients": info.get('connected_clients', 0),
            "total_commands_processed": info.get('total_commands_processed', 0),
            "keyspace_hits": info.get('keyspace_hits', 0),
            "keyspace_misses": info.get('keyspace_misses', 0)
        }
    except Exception as e:
        return {"available": False, "error": str(e)}