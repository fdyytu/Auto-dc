"""
Simple Cache Manager
Cache manager sederhana untuk keperluan analytics
"""

import json
import time
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

class CacheManager:
    """Simple in-memory cache manager"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.debug("CacheManager initialized")
    
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
        cache_count = len(self._cache)
        self._cache.clear()
        logger.info(f"🧹 Cache cleared: {cache_count} entries removed")
    
    async def clear_temporary(self) -> int:
        """Clear only temporary cache entries"""
        removed_count = 0
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if not entry.get('permanent', False):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
            removed_count += 1
        
        logger.info(f"🧹 Temporary cache cleared: {removed_count} entries removed")
        return removed_count
    
    async def clear_expired(self) -> int:
        """Clear expired cache entries"""
        removed_count = 0
        current_time = time.time()
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if entry.get('expires_at', float('inf')) <= current_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
            removed_count += 1
        
        logger.info(f"🧹 Expired cache cleared: {removed_count} entries removed")
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_keys = len(self._cache)
        permanent_keys = sum(1 for entry in self._cache.values() if entry.get('permanent', False))
        current_time = time.time()
        expired_keys = sum(1 for entry in self._cache.values() 
                          if entry.get('expires_at', float('inf')) <= current_time)
        
        return {
            'total_keys': total_keys,
            'permanent_keys': permanent_keys,
            'temporary_keys': total_keys - permanent_keys,
            'expired_keys': expired_keys,
            'active_keys': total_keys - expired_keys
        }
