"""
Caching Utilities

LRU cache with TTL support and cache invalidation.
"""

import time
import hashlib
import json
from typing import Any, Callable, Optional, Dict
from functools import wraps, lru_cache
from pathlib import Path
import pickle


class TTLCache:
    """
    Time-to-live cache implementation.
    
    Stores values with expiration times and automatically
    evicts expired entries.
    """
    
    def __init__(self, ttl: float = 3600.0, max_size: int = 128):
        """
        Initialize TTL cache.
        
        Args:
            ttl: Time to live in seconds
            max_size: Maximum number of entries
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        if time.time() > expiry:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        expiry = time.time() + self.ttl
        self._cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate specific cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        self._cache.pop(key, None)
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Cache key string
    """
    # Create a stable representation
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    
    # Serialize to JSON for hashing
    key_str = json.dumps(key_data, default=str, sort_keys=True)
    
    # Hash for shorter key
    return hashlib.md5(key_str.encode()).hexdigest()


def cached_with_ttl(ttl: float = 3600.0, max_size: int = 128):
    """
    Decorator for caching function results with TTL.
    
    Args:
        ttl: Time to live in seconds
        max_size: Maximum cache size
    
    Usage:
        @cached_with_ttl(ttl=3600)
        def expensive_function(arg1, arg2):
            ...
    """
    cache = TTLCache(ttl=ttl, max_size=max_size)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(key, result)
            
            return result
        
        return wrapper
    
    return decorator


class FileCache:
    """
    File-based cache for persistent storage.
    
    Useful for caching across application restarts.
    """
    
    def __init__(self, cache_dir: Path, ttl: float = 3600.0):
        """
        Initialize file cache.
        
        Args:
            cache_dir: Directory for cache files
            ttl: Time to live in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        # Sanitize key for filename
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from file cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            # Check modification time
            mtime = cache_path.stat().st_mtime
            if time.time() - mtime > self.ttl:
                cache_path.unlink()
                return None
            
            # Load cached value
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            # If anything goes wrong, remove corrupted cache
            cache_path.unlink()
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in file cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception:
            # Silently fail cache writes
            pass
    
    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate specific cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()

