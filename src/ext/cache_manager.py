"""
Simple Cache Manager
Cache manager sederhana untuk keperluan analytics
"""

import json
import time
from typing import Any, Optional, Dict

class CacheManager:
    """Simple in-memory cache manager"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            cache_entry = self._cache[key]
            # Check if expired
            if cache_entry.get('expires_at', float('inf')) > time.time():
                return cache_entry['value']
            else:
                # Remove expired entry
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, expires_in: int = 3600, permanent: bool = False) -> None:
        """Set value in cache"""
        expires_at = float('inf') if permanent else time.time() + expires_in
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'permanent': permanent
        }
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_keys = len(self._cache)
        permanent_keys = sum(1 for entry in self._cache.values() if entry.get('permanent', False))
        return {
            'total_keys': total_keys,
            'permanent_keys': permanent_keys,
            'temporary_keys': total_keys - permanent_keys
        }
