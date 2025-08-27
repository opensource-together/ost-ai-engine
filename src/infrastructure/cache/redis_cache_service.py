"""
Simplified Redis cache service for the data engine.

Uses standard Python libraries:
- redis-py for Redis operations
- cachetools for memory caching
- json for serialization
"""

import json
import time
from typing import Any, Optional, Dict
from cachetools import TTLCache

import redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from src.infrastructure.config import settings
from src.infrastructure.logger import log


class SimpleRedisCacheService:
    """
    Simplified Redis cache service using standard libraries.
    
    Features:
    - Two-level caching (Memory + Redis)
    - JSON serialization
    - Automatic TTL management
    - Error handling
    - Performance monitoring
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache service.
        
        Args:
            redis_url: Redis connection URL (default from settings)
        """
        self.redis_url = redis_url or settings.REDIS_CACHE_URL
        
        # Memory cache (L1) - 1000 items, 5 minutes TTL
        self.memory_cache = TTLCache(maxsize=1000, ttl=300)
        
        # Redis client (L2)
        self._redis_client: Optional[redis.Redis] = None
        self._init_redis_connection()

    def _init_redis_connection(self):
        """Initialize Redis connection with error handling."""
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,  # Auto-decode to strings
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            # Test connection
            self._redis_client.ping()
            log.info("✅ Redis cache connection established")
            
        except Exception as e:
            log.error(f"❌ Failed to connect to Redis: {e}")
            self._redis_client = None

    def _generate_key(self, key: str, namespace: str = "default") -> str:
        """Generate namespaced cache key."""
        return f"{namespace}:{key}"

    def _serialize(self, data: Any) -> str:
        """Serialize data to JSON string."""
        try:
            return json.dumps(data, default=str)
        except (TypeError, ValueError) as e:
            log.warning(f"⚠️ Serialization failed, using string: {e}")
            return str(data)

    def _deserialize(self, data: str) -> Any:
        """Deserialize data from JSON string."""
        try:
            return json.loads(data)
        except (TypeError, ValueError) as e:
            log.warning(f"⚠️ Deserialization failed, returning raw data: {e}")
            return data

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get value from cache (L1: Memory, L2: Redis).
        
        Args:
            key: Cache key
            namespace: Optional namespace
            
        Returns:
            Cached value or None if not found
        """
        start_time = time.time()
        cache_key = self._generate_key(key, namespace)
        
        try:
            # L1: Try memory cache first
            if cache_key in self.memory_cache:
                log.debug(f"🎯 Memory cache hit: {cache_key}")
                return self.memory_cache[cache_key]
            
            # L2: Try Redis cache
            if self._redis_client:
                try:
                    data = self._redis_client.get(cache_key)
                    if data:
                        value = self._deserialize(data)
                        # Store in memory cache for future access
                        self.memory_cache[cache_key] = value
                        log.debug(f"🎯 Redis cache hit: {cache_key}")
                        return value
                        
                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"❌ Redis error during get: {e}")
            
            log.debug(f"❌ Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            log.error(f"❌ Cache get operation failed: {e}")
            return None
        finally:
            duration = (time.time() - start_time) * 1000
            log.debug(f"⏱️ Cache get took {duration:.2f}ms")

    def set(self, key: str, value: Any, ttl: int = 3600, namespace: str = "default") -> bool:
        """
        Set value in cache (both L1 and L2).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
            namespace: Optional namespace
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        cache_key = self._generate_key(key, namespace)
        
        try:
            # Serialize data
            serialized_data = self._serialize(value)
            
            # L1: Store in memory cache
            self.memory_cache[cache_key] = value
            
            # L2: Store in Redis
            if self._redis_client:
                try:
                    self._redis_client.setex(cache_key, ttl, serialized_data)
                    log.debug(f"💾 Cache set: {cache_key} (TTL: {ttl}s)")
                    return True
                    
                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"❌ Redis error during set: {e}")
                    return False
            
            return True
            
        except Exception as e:
            log.error(f"❌ Cache set operation failed: {e}")
            return False
        finally:
            duration = (time.time() - start_time) * 1000
            log.debug(f"⏱️ Cache set took {duration:.2f}ms")

    def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete value from cache (both L1 and L2).
        
        Args:
            key: Cache key
            namespace: Optional namespace
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(key, namespace)
        
        try:
            # L1: Remove from memory cache
            self.memory_cache.pop(cache_key, None)
            
            # L2: Remove from Redis
            if self._redis_client:
                try:
                    result = self._redis_client.delete(cache_key)
                    log.debug(f"🗑️ Cache delete: {cache_key}")
                    return result > 0
                    
                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"❌ Redis error during delete: {e}")
                    return False
            
            return True
            
        except Exception as e:
            log.error(f"❌ Cache delete operation failed: {e}")
            return False

    def mget(self, keys: list[str], namespace: str = "default") -> Dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            namespace: Optional namespace
            
        Returns:
            Dictionary of key-value pairs
        """
        results = {}
        
        try:
            # L1: Try memory cache first
            for key in keys:
                cache_key = self._generate_key(key, namespace)
                if cache_key in self.memory_cache:
                    results[key] = self.memory_cache[cache_key]
            
            # L2: Try Redis for remaining keys
            remaining_keys = [k for k in keys if k not in results]
            if remaining_keys and self._redis_client:
                try:
                    cache_keys = [self._generate_key(k, namespace) for k in remaining_keys]
                    redis_data = self._redis_client.mget(cache_keys)
                    
                    for key, data in zip(remaining_keys, redis_data):
                        if data:
                            value = self._deserialize(data)
                            results[key] = value
                            # Store in memory cache
                            cache_key = self._generate_key(key, namespace)
                            self.memory_cache[cache_key] = value
                            
                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"❌ Redis error during mget: {e}")
            
            log.debug(f"📦 Batch get: {len(results)}/{len(keys)} found")
            return results
            
        except Exception as e:
            log.error(f"❌ Cache mget operation failed: {e}")
            return {}

    def mset(self, data: Dict[str, Any], ttl: int = 3600, namespace: str = "default") -> bool:
        """
        Set multiple values in cache.
        
        Args:
            data: Dictionary of key-value pairs
            ttl: Time to live in seconds
            namespace: Optional namespace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # L1: Store in memory cache
            for key, value in data.items():
                cache_key = self._generate_key(key, namespace)
                self.memory_cache[cache_key] = value
            
            # L2: Store in Redis
            if self._redis_client:
                try:
                    # Use pipeline for better performance
                    pipe = self._redis_client.pipeline()
                    for key, value in data.items():
                        cache_key = self._generate_key(key, namespace)
                        serialized_data = self._serialize(value)
                        pipe.setex(cache_key, ttl, serialized_data)
                    pipe.execute()
                    
                    log.debug(f"📦 Batch set: {len(data)} items")
                    return True
                    
                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"❌ Redis error during mset: {e}")
                    return False
            
            return True
            
        except Exception as e:
            log.error(f"❌ Cache mset operation failed: {e}")
            return False

    def clear_memory_cache(self):
        """Clear memory cache."""
        self.memory_cache.clear()
        log.info("🧹 Memory cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = {
                "memory_cache_size": len(self.memory_cache),
                "memory_cache_ttl": self.memory_cache.ttl,
                "redis_connected": self._redis_client is not None,
            }
            
            if self._redis_client:
                try:
                    info = self._redis_client.info()
                    stats.update({
                        "redis_used_memory": info.get("used_memory", 0),
                        "redis_connected_clients": info.get("connected_clients", 0),
                        "redis_keyspace_hits": info.get("keyspace_hits", 0),
                        "redis_keyspace_misses": info.get("keyspace_misses", 0),
                    })
                except Exception as e:
                    log.warning(f"⚠️ Could not get Redis info: {e}")
            
            return stats
            
        except Exception as e:
            log.error(f"❌ Failed to get cache stats: {e}")
            return {}


# Global cache service instance
cache_service = SimpleRedisCacheService()
