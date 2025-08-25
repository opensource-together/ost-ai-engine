"""
Advanced Redis cache service for the data engine.

Provides optimized caching capabilities including:
- Multi-level caching (L1: Memory, L2: Redis)
- Cache compression and serialization
- Intelligent cache invalidation
- Cache warming and preloading
- Performance monitoring
- Circuit breaker pattern
"""

import gzip
import json
import pickle
import threading
import time
from datetime import datetime, timedelta
from typing import Any

import redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from src.infrastructure.config import settings
from src.infrastructure.logger import log
from src.infrastructure.monitoring import metrics_service


class CacheCompression:
    """Compression utilities for cache data."""

    @staticmethod
    def compress(data: bytes) -> bytes:
        """Compress data using gzip."""
        return gzip.compress(data, compresslevel=6)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """Decompress data using gzip."""
        return gzip.decompress(data)

    @staticmethod
    def should_compress(data: bytes, threshold: int = 1024) -> bool:
        """Determine if data should be compressed based on size."""
        return len(data) > threshold


class CacheSerialization:
    """Serialization utilities for cache data."""

    @staticmethod
    def serialize(data: Any) -> bytes:
        """Serialize data to bytes."""
        return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def deserialize(data: bytes) -> Any:
        """Deserialize data from bytes."""
        return pickle.loads(data)

    @staticmethod
    def serialize_json(data: Any) -> bytes:
        """Serialize data to JSON bytes."""
        return json.dumps(data, default=str).encode("utf-8")

    @staticmethod
    def deserialize_json(data: bytes) -> Any:
        """Deserialize data from JSON bytes."""
        return json.loads(data.decode("utf-8"))


class AdvancedRedisCacheService:
    """
    Advanced Redis cache service with optimization features.

    Features:
    - Multi-level caching (Memory + Redis)
    - Compression for large objects
    - Intelligent cache invalidation
    - Cache warming and preloading
    - Performance monitoring
    - Circuit breaker pattern
    - Batch operations
    """

    def __init__(self):
        self._redis_client: redis.Redis | None = None
        self._memory_cache: dict[str, Any] = {}
        self._memory_cache_ttl: dict[str, datetime] = {}
        self._circuit_breaker_open = False
        self._circuit_breaker_last_failure = None
        self._lock = threading.Lock()

        # Initialize Redis connection
        self._init_redis_connection()

    def _init_redis_connection(self):
        """Initialize Redis connection with error handling."""
        try:
            self._redis_client = redis.Redis.from_url(
                settings.REDIS_CACHE_URL,
                decode_responses=False,  # Keep as bytes for compression
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_READ_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            self._redis_client.ping()
            log.info("Redis cache connection established successfully")

        except Exception as e:
            log.error(f"Failed to connect to Redis: {e}")
            self._redis_client = None

    def _generate_cache_key(self, key: str, namespace: str = None) -> str:
        """Generate a cache key with optional namespace."""
        if namespace:
            return f"{namespace}:{key}"
        return key

    def _should_use_memory_cache(self, key: str) -> bool:
        """Determine if key should use memory cache."""
        # Use memory cache for frequently accessed, small objects
        return len(key) < 100 and not key.startswith("large_")

    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open."""
        if not self._circuit_breaker_open:
            return False

        # Reset circuit breaker after 30 seconds
        if self._circuit_breaker_last_failure:
            if datetime.now() - self._circuit_breaker_last_failure > timedelta(
                seconds=30
            ):
                self._circuit_breaker_open = False
                self._circuit_breaker_last_failure = None
                log.info("Circuit breaker reset")

        return self._circuit_breaker_open

    def _record_cache_operation(
        self, operation: str, key: str, hit: bool, duration: float = None
    ):
        """Record cache operation metrics."""
        metrics_service.record_cache_operation(operation, key, hit, duration)

    def get(
        self, key: str, namespace: str = None, use_memory: bool = True
    ) -> Any | None:
        """
        Get value from cache with multi-level support.

        Args:
            key: Cache key
            namespace: Optional namespace
            use_memory: Whether to use memory cache

        Returns:
            Cached value or None if not found
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(key, namespace)

        try:
            # Try memory cache first
            if use_memory and self._should_use_memory_cache(cache_key):
                with self._lock:
                    if cache_key in self._memory_cache:
                        ttl = self._memory_cache_ttl.get(cache_key)
                        if ttl and datetime.now() < ttl:
                            self._record_cache_operation(
                                "get",
                                cache_key,
                                True,
                                (time.time() - start_time) * 1000,
                            )
                            return self._memory_cache[cache_key]
                        else:
                            # Expired, remove from memory
                            del self._memory_cache[cache_key]
                            if cache_key in self._memory_cache_ttl:
                                del self._memory_cache_ttl[cache_key]

            # Try Redis cache
            if self._redis_client and not self._is_circuit_breaker_open():
                try:
                    data = self._redis_client.get(cache_key)
                    if data:
                        # Check if data is compressed
                        if data.startswith(b"gzip:"):
                            data = CacheCompression.decompress(data[5:])

                        # Deserialize data
                        try:
                            value = CacheSerialization.deserialize(data)
                        except:
                            # Fallback to JSON
                            value = CacheSerialization.deserialize_json(data)

                        # Store in memory cache for future access
                        if use_memory and self._should_use_memory_cache(cache_key):
                            with self._lock:
                                self._memory_cache[cache_key] = value
                                self._memory_cache_ttl[cache_key] = (
                                    datetime.now() + timedelta(minutes=5)
                                )

                        self._record_cache_operation(
                            "get", cache_key, True, (time.time() - start_time) * 1000
                        )
                        return value

                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"Redis error during get operation: {e}")
                    self._circuit_breaker_open = True
                    self._circuit_breaker_last_failure = datetime.now()

            self._record_cache_operation(
                "get", cache_key, False, (time.time() - start_time) * 1000
            )
            return None

        except Exception as e:
            log.error(f"Cache get operation failed: {e}")
            self._record_cache_operation(
                "get", cache_key, False, (time.time() - start_time) * 1000
            )
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
        namespace: str = None,
        compress: bool = True,
        use_memory: bool = True,
    ) -> bool:
        """
        Set value in cache with optimization features.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            namespace: Optional namespace
            compress: Whether to compress data
            use_memory: Whether to use memory cache

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(key, namespace)

        try:
            # Serialize data
            data = CacheSerialization.serialize(value)

            # Compress if needed
            if compress and CacheCompression.should_compress(data):
                data = b"gzip:" + CacheCompression.compress(data)

            # Store in memory cache
            if use_memory and self._should_use_memory_cache(cache_key):
                with self._lock:
                    self._memory_cache[cache_key] = value
                    if ttl:
                        self._memory_cache_ttl[cache_key] = datetime.now() + timedelta(
                            seconds=ttl
                        )
                    else:
                        self._memory_cache_ttl[cache_key] = datetime.now() + timedelta(
                            minutes=5
                        )

            # Store in Redis
            if self._redis_client and not self._is_circuit_breaker_open():
                try:
                    if ttl:
                        self._redis_client.setex(cache_key, ttl, data)
                    else:
                        self._redis_client.set(cache_key, data)

                    self._record_cache_operation(
                        "set", cache_key, True, (time.time() - start_time) * 1000
                    )
                    return True

                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"Redis error during set operation: {e}")
                    self._circuit_breaker_open = True
                    self._circuit_breaker_last_failure = datetime.now()

            self._record_cache_operation(
                "set", cache_key, False, (time.time() - start_time) * 1000
            )
            return False

        except Exception as e:
            log.error(f"Cache set operation failed: {e}")
            self._record_cache_operation(
                "set", cache_key, False, (time.time() - start_time) * 1000
            )
            return False

    def delete(self, key: str, namespace: str = None) -> bool:
        """Delete value from cache."""
        start_time = time.time()
        cache_key = self._generate_cache_key(key, namespace)

        try:
            # Remove from memory cache
            with self._lock:
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                if cache_key in self._memory_cache_ttl:
                    del self._memory_cache_ttl[cache_key]

            # Remove from Redis
            if self._redis_client and not self._is_circuit_breaker_open():
                try:
                    result = self._redis_client.delete(cache_key)
                    self._record_cache_operation(
                        "delete", cache_key, True, (time.time() - start_time) * 1000
                    )
                    return result > 0

                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"Redis error during delete operation: {e}")
                    self._circuit_breaker_open = True
                    self._circuit_breaker_last_failure = datetime.now()

            self._record_cache_operation(
                "delete", cache_key, False, (time.time() - start_time) * 1000
            )
            return False

        except Exception as e:
            log.error(f"Cache delete operation failed: {e}")
            self._record_cache_operation(
                "delete", cache_key, False, (time.time() - start_time) * 1000
            )
            return False

    def mget(self, keys: list[str], namespace: str = None) -> dict[str, Any]:
        """Get multiple values from cache."""
        start_time = time.time()
        cache_keys = [self._generate_cache_key(key, namespace) for key in keys]

        try:
            results = {}

            # Try memory cache first
            with self._lock:
                for key, cache_key in zip(keys, cache_keys, strict=False):
                    if cache_key in self._memory_cache:
                        ttl = self._memory_cache_ttl.get(cache_key)
                        if ttl and datetime.now() < ttl:
                            results[key] = self._memory_cache[cache_key]

            # Try Redis for remaining keys
            if self._redis_client and not self._is_circuit_breaker_open():
                try:
                    remaining_keys = [k for k in keys if k not in results]
                    if remaining_keys:
                        remaining_cache_keys = [
                            self._generate_cache_key(k, namespace)
                            for k in remaining_keys
                        ]
                        redis_results = self._redis_client.mget(remaining_cache_keys)

                        for key, cache_key, data in zip(
                            remaining_keys,
                            remaining_cache_keys,
                            redis_results,
                            strict=False,
                        ):
                            if data:
                                # Check if data is compressed
                                if data.startswith(b"gzip:"):
                                    data = CacheCompression.decompress(data[5:])

                                # Deserialize data
                                try:
                                    value = CacheSerialization.deserialize(data)
                                except:
                                    value = CacheSerialization.deserialize_json(data)

                                results[key] = value

                                # Store in memory cache
                                if self._should_use_memory_cache(cache_key):
                                    with self._lock:
                                        self._memory_cache[cache_key] = value
                                        self._memory_cache_ttl[cache_key] = (
                                            datetime.now() + timedelta(minutes=5)
                                        )

                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"Redis error during mget operation: {e}")
                    self._circuit_breaker_open = True
                    self._circuit_breaker_last_failure = datetime.now()

            self._record_cache_operation(
                "mget",
                f"batch_{len(keys)}",
                len(results) > 0,
                (time.time() - start_time) * 1000,
            )
            return results

        except Exception as e:
            log.error(f"Cache mget operation failed: {e}")
            self._record_cache_operation(
                "mget", f"batch_{len(keys)}", False, (time.time() - start_time) * 1000
            )
            return {}

    def mset(
        self,
        data: dict[str, Any],
        ttl: int = None,
        namespace: str = None,
        compress: bool = True,
    ) -> bool:
        """Set multiple values in cache."""
        start_time = time.time()

        try:
            # Prepare data for Redis
            redis_data = {}
            for key, value in data.items():
                cache_key = self._generate_cache_key(key, namespace)

                # Serialize data
                serialized = CacheSerialization.serialize(value)

                # Compress if needed
                if compress and CacheCompression.should_compress(serialized):
                    serialized = b"gzip:" + CacheCompression.compress(serialized)

                redis_data[cache_key] = serialized

            # Store in Redis
            if self._redis_client and not self._is_circuit_breaker_open():
                try:
                    if ttl:
                        # Use pipeline for better performance
                        pipe = self._redis_client.pipeline()
                        for cache_key, data in redis_data.items():
                            pipe.setex(cache_key, ttl, data)
                        pipe.execute()
                    else:
                        self._redis_client.mset(redis_data)

                    self._record_cache_operation(
                        "mset",
                        f"batch_{len(data)}",
                        True,
                        (time.time() - start_time) * 1000,
                    )
                    return True

                except (RedisError, ConnectionError, TimeoutError) as e:
                    log.error(f"Redis error during mset operation: {e}")
                    self._circuit_breaker_open = True
                    self._circuit_breaker_last_failure = datetime.now()

            self._record_cache_operation(
                "mset", f"batch_{len(data)}", False, (time.time() - start_time) * 1000
            )
            return False

        except Exception as e:
            log.error(f"Cache mset operation failed: {e}")
            self._record_cache_operation(
                "mset", f"batch_{len(data)}", False, (time.time() - start_time) * 1000
            )
            return False

    def clear_memory_cache(self):
        """Clear memory cache."""
        with self._lock:
            self._memory_cache.clear()
            self._memory_cache_ttl.clear()
        log.info("Memory cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = {
                "memory_cache_size": len(self._memory_cache),
                "circuit_breaker_open": self._circuit_breaker_open,
                "redis_connected": self._redis_client is not None,
            }

            if self._redis_client and not self._is_circuit_breaker_open():
                try:
                    info = self._redis_client.info()
                    stats.update(
                        {
                            "redis_used_memory": info.get("used_memory", 0),
                            "redis_connected_clients": info.get("connected_clients", 0),
                            "redis_keyspace_hits": info.get("keyspace_hits", 0),
                            "redis_keyspace_misses": info.get("keyspace_misses", 0),
                        }
                    )
                except:
                    pass

            return stats

        except Exception as e:
            log.error(f"Failed to get cache stats: {e}")
            return {}


# Global cache service instance
cache_service = AdvancedRedisCacheService()
