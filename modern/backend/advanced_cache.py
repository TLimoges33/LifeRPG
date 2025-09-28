"""
Advanced caching system for LifeRPG with multi-level cache strategy.
"""
import json
import time
import hashlib
import functools
from typing import Any, Dict, Optional, Union, Callable
from datetime import datetime, timedelta
from cachetools import TTLCache
import asyncio
import os

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class AdvancedCacheManager:
    """Multi-level cache manager with Redis and memory fallback."""
    
    def __init__(self, redis_url: Optional[str] = None):
        # Memory cache (L1) - fastest access
        self.memory_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
        
        # Redis cache (L2) - persistent, shared
        self.redis_client = None
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
        
        self.stats = {
            'memory_hits': 0,
            'memory_misses': 0,
            'redis_hits': 0,
            'redis_misses': 0,
            'total_requests': 0
        }
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from function arguments."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback strategy."""
        self.stats['total_requests'] += 1
        
        # L1: Check memory cache first
        if key in self.memory_cache:
            self.stats['memory_hits'] += 1
            return self.memory_cache[key]
        
        self.stats['memory_misses'] += 1
        
        # L2: Check Redis cache
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    self.stats['redis_hits'] += 1
                    # Deserialize and populate memory cache
                    deserialized = json.loads(value)
                    self.memory_cache[key] = deserialized
                    return deserialized
            except Exception:
                pass
        
        self.stats['redis_misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in both cache levels."""
        try:
            # Set in memory cache
            self.memory_cache[key] = value
            
            # Set in Redis cache
            if self.redis_client:
                serialized = json.dumps(value, default=str)
                await self.redis_client.setex(key, ttl, serialized)
            
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from both cache levels."""
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Remove from Redis
            if self.redis_client:
                await self.redis_client.delete(key)
            
            return True
        except Exception:
            return False
    
    async def get_with_fallback(self, key: str, fallback_func: Callable, ttl: int = 300) -> Any:
        """Get from cache or execute fallback function and cache result."""
        value = await self.get(key)
        if value is not None:
            return value
        
        # Execute fallback function
        if asyncio.iscoroutinefunction(fallback_func):
            result = await fallback_func()
        else:
            result = fallback_func()
        
        # Cache the result
        await self.set(key, result, ttl)
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total = self.stats['total_requests']
        if total == 0:
            return self.stats
        
        memory_hit_rate = self.stats['memory_hits'] / total
        redis_hit_rate = self.stats['redis_hits'] / total
        overall_hit_rate = (self.stats['memory_hits'] + self.stats['redis_hits']) / total
        
        return {
            **self.stats,
            'memory_hit_rate': memory_hit_rate,
            'redis_hit_rate': redis_hit_rate,
            'overall_hit_rate': overall_hit_rate,
            'memory_cache_size': len(self.memory_cache)
        }
    
    async def clear_all(self) -> bool:
        """Clear all cache levels."""
        try:
            self.memory_cache.clear()
            if self.redis_client:
                await self.redis_client.flushdb()
            return True
        except Exception:
            return False


# Global cache instance
cache_manager = AdvancedCacheManager(
    redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)


def cached_response(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function responses."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )
            
            # Try to get from cache
            result = await cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache_manager.set(cache_key, result, ttl)
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, use asyncio.run
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_key(*key_parts: str) -> str:
    """Generate a cache key from parts."""
    return ":".join(str(part) for part in key_parts)


class QueryCache:
    """Specialized cache for database queries."""
    
    @staticmethod
    @cached_response(ttl=600, key_prefix="query")
    def get_user_habits(user_id: int, status: str = "active"):
        """Cache user habits query."""
        # This will be implemented in the analytics module
        pass
    
    @staticmethod
    @cached_response(ttl=300, key_prefix="analytics")  
    def get_habit_completion_stats(user_id: int, days: int = 30):
        """Cache habit completion analytics."""
        pass
    
    @staticmethod
    @cached_response(ttl=900, key_prefix="leaderboard")
    def get_leaderboard_data(timeframe: str = "weekly"):
        """Cache leaderboard data."""
        pass


class CacheWarmer:
    """Proactively warm cache with commonly requested data."""
    
    def __init__(self, cache_manager: AdvancedCacheManager):
        self.cache_manager = cache_manager
    
    async def warm_user_data(self, user_id: int):
        """Pre-populate cache with user's most common data."""
        # Warm user habits
        await self.cache_manager.get_with_fallback(
            f"user:{user_id}:habits",
            lambda: self._fetch_user_habits(user_id),
            ttl=600
        )
        
        # Warm user analytics
        await self.cache_manager.get_with_fallback(
            f"user:{user_id}:analytics:30d",
            lambda: self._fetch_user_analytics(user_id, 30),
            ttl=300
        )
    
    def _fetch_user_habits(self, user_id: int):
        """Fetch user habits (placeholder - to be implemented)."""
        return []
    
    def _fetch_user_analytics(self, user_id: int, days: int):
        """Fetch user analytics (placeholder - to be implemented)."""
        return {}


# Initialize cache warmer
cache_warmer = CacheWarmer(cache_manager)