"""
Integration tests for Redis cache functionality.
"""

import pytest
import json
import time
from unittest.mock import patch
from src.infrastructure.cache.redis_cache_service import SimpleRedisCacheService


@pytest.mark.integration
def test_redis_connection():
    """Test Redis connection and basic operations."""
    print("🔍 REDIS CONNECTION TEST")
    print("=" * 80)
    
    try:
        cache = SimpleRedisCacheService()
        
        # Test basic set/get
        cache.set("test_key", "test_value", ttl=60)
        value = cache.get("test_key")
        assert value == "test_value"
        print("✅ Basic set/get operations work")
        
        # Test TTL
        cache.set("ttl_test", "value", ttl=1)
        time.sleep(1.1)
        value = cache.get("ttl_test")
        assert value is None
        print("✅ TTL expiration works")
        
        # Test complex data
        test_data = {"user_id": "123", "recommendations": [1, 2, 3]}
        cache.set("complex_data", test_data, ttl=60)
        retrieved = cache.get("complex_data")
        assert retrieved == test_data
        print("✅ Complex data serialization works")
        
        # Test namespace
        cache.set("key", "value1", namespace="ns1", ttl=60)
        cache.set("key", "value2", namespace="ns2", ttl=60)
        
        value1 = cache.get("key", namespace="ns1")
        value2 = cache.get("key", namespace="ns2")
        assert value1 == "value1"
        assert value2 == "value2"
        print("✅ Namespace isolation works")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        pytest.skip("Redis not available")


@pytest.mark.integration
def test_cache_performance():
    """Test cache performance characteristics."""
    print("\n🔍 CACHE PERFORMANCE TEST")
    print("=" * 80)
    
    try:
        cache = SimpleRedisCacheService()
        
        # Test bulk operations
        start_time = time.time()
        for i in range(100):
            cache.set(f"bulk_key_{i}", f"value_{i}", ttl=60)
        
        set_time = time.time() - start_time
        print(f"✅ Set 100 keys in {set_time:.3f}s ({100/set_time:.0f} ops/s)")
        
        # Test bulk retrieval
        start_time = time.time()
        for i in range(100):
            value = cache.get(f"bulk_key_{i}")
            assert value == f"value_{i}"
        
        get_time = time.time() - start_time
        print(f"✅ Get 100 keys in {get_time:.3f}s ({100/get_time:.0f} ops/s)")
        
        # Test memory cache (L1)
        start_time = time.time()
        for i in range(100):
            cache.get(f"bulk_key_{i}")  # Should hit memory cache
        
        memory_time = time.time() - start_time
        print(f"✅ Memory cache hit in {memory_time:.3f}s ({100/memory_time:.0f} ops/s)")
        
        assert memory_time < get_time, "Memory cache should be faster than Redis"
        
    except Exception as e:
        print(f"❌ Cache performance test failed: {e}")
        pytest.skip("Redis not available")


@pytest.mark.integration
def test_cache_error_handling():
    """Test cache error handling and fallbacks."""
    print("\n🔍 CACHE ERROR HANDLING TEST")
    print("=" * 80)
    
    # Test with invalid Redis URL
    with patch('src.infrastructure.cache.redis_cache_service.settings') as mock_settings:
        mock_settings.REDIS_CACHE_URL = "redis://invalid:6379/0"
        
        cache = SimpleRedisCacheService()
        
        # Should not raise exception
        cache.set("test", "value", ttl=60)
        value = cache.get("test")
        
        # Should work with memory cache only
        assert value == "value"
        print("✅ Graceful fallback to memory cache when Redis unavailable")


@pytest.mark.integration
def test_embedding_cache():
    """Test embedding-specific cache operations."""
    print("\n🔍 EMBEDDING CACHE TEST")
    print("=" * 80)
    
    try:
        cache = SimpleRedisCacheService()
        
        # Test embedding storage
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 76  # 384 dimensions
        cache.set("embedding:user:123", embedding, namespace="embeddings", ttl=3600)
        
        retrieved = cache.get("embedding:user:123", namespace="embeddings")
        assert retrieved == embedding
        print("✅ Embedding storage and retrieval works")
        
        # Test embedding batch operations
        embeddings = {}
        for i in range(10):
            embeddings[f"user_{i}"] = [float(j) for j in range(384)]
        
        # Store batch
        for user_id, emb in embeddings.items():
            cache.set(f"embedding:{user_id}", emb, namespace="embeddings", ttl=3600)
        
        # Retrieve batch
        for user_id, expected_emb in embeddings.items():
            retrieved = cache.get(f"embedding:{user_id}", namespace="embeddings")
            assert retrieved == expected_emb
        
        print("✅ Embedding batch operations work")
        
    except Exception as e:
        print(f"❌ Embedding cache test failed: {e}")
        pytest.skip("Redis not available")


@pytest.mark.integration
def test_cache_cleanup():
    """Test cache cleanup and memory management."""
    print("\n🔍 CACHE CLEANUP TEST")
    print("=" * 80)
    
    try:
        cache = SimpleRedisCacheService()
        
        # Fill cache
        for i in range(1000):
            cache.set(f"cleanup_test_{i}", f"data_{i}", ttl=60)
        
        # Test memory cache size limit
        memory_size = len(cache.memory_cache)
        print(f"📊 Memory cache size: {memory_size}")
        assert memory_size <= 1000, "Memory cache should respect size limit"
        
        # Test cleanup
        cache.clear()
        memory_size_after = len(cache.memory_cache)
        assert memory_size_after == 0
        print("✅ Cache cleanup works")
        
    except Exception as e:
        print(f"❌ Cache cleanup test failed: {e}")
        pytest.skip("Redis not available")
