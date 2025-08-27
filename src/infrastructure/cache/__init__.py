"""
Cache infrastructure package for the data engine.

Provides simplified caching capabilities using standard libraries:
- Two-level caching (Memory + Redis)
- JSON serialization
- Automatic TTL management
- Error handling
"""

from .redis_cache_service import SimpleRedisCacheService, cache_service

__all__ = ["cache_service", "SimpleRedisCacheService"]
