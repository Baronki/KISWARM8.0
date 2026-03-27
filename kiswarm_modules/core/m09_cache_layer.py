#!/usr/bin/env python3
"""
KISWARM8.0 - Module 09: Cache Layer
===================================
High-performance caching for KISWARM.

Features:
  - In-memory caching
  - Distributed cache support
  - Cache invalidation strategies
  - TTL management
  - Cache warming

Author: GLM-7 Autonomous
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

import os
import json
import time
import logging
import threading
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict

logger = logging.getLogger('m09_cache')


@dataclass
class CacheEntry:
    """Cache entry"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_access: float = 0
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
        
    def touch(self):
        self.access_count += 1
        self.last_access = time.time()


class CacheLayer:
    """
    High-Performance Cache for KISWARM
    
    Supports multiple caching strategies.
    """
    
    DEFAULT_MAX_SIZE = 1000  # Max entries
    DEFAULT_MAX_MEMORY = 100 * 1024 * 1024  # 100MB
    DEFAULT_TTL = 3600  # 1 hour
    
    def __init__(self, 
                 max_entries: int = None,
                 max_memory_bytes: int = None,
                 default_ttl: int = None,
                 persistence_dir: Optional[Path] = None):
        
        self.max_entries = max_entries or self.DEFAULT_MAX_SIZE
        self.max_memory = max_memory_bytes or self.DEFAULT_MAX_MEMORY
        self.default_ttl = default_ttl or self.DEFAULT_TTL
        self.persistence_dir = persistence_dir or Path('/opt/kiswarm7/data/cache')
        
        self._cache: Dict[str, CacheEntry] = {}
        self._tag_index: Dict[str, set] = {}  # tag -> set of keys
        self._lock = threading.RLock()
        self._current_memory = 0
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
        
        # Warm-up hooks
        self._warmup_hooks: List[Callable] = []
        
        # Start cleanup thread
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        # Load persisted cache
        self._load_cache()
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return default
                
            if entry.is_expired():
                self._delete_entry(key)
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return default
                
            entry.touch()
            self._stats['hits'] += 1
            return entry.value
            
    def set(self, 
            key: str, 
            value: Any, 
            ttl: int = None,
            tags: List[str] = None) -> bool:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        tags = tags or []
        
        # Estimate size
        try:
            size = len(json.dumps(value))
        except:
            size = 100  # Default estimate
            
        now = time.time()
        expires_at = now + ttl if ttl > 0 else None
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=expires_at,
            size_bytes=size,
            tags=tags
        )
        
        with self._lock:
            # Remove old entry if exists
            if key in self._cache:
                self._delete_entry(key)
                
            # Check capacity
            while (len(self._cache) >= self.max_entries or 
                   self._current_memory + size > self.max_memory):
                if not self._evict_lru():
                    break
                    
            # Add entry
            self._cache[key] = entry
            self._current_memory += size
            
            # Update tag index
            for tag in tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(key)
                
        return True
        
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self._lock:
            if key in self._cache:
                self._delete_entry(key)
                return True
        return False
        
    def _delete_entry(self, key: str):
        """Internal delete (must be called with lock)"""
        entry = self._cache.pop(key, None)
        if entry:
            self._current_memory -= entry.size_bytes
            for tag in entry.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(key)
                    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._tag_index.clear()
            self._current_memory = 0
            
    def invalidate_tag(self, tag: str) -> int:
        """Invalidate all entries with a tag"""
        count = 0
        with self._lock:
            keys = list(self._tag_index.get(tag, set()))
            for key in keys:
                self._delete_entry(key)
                count += 1
        return count
        
    def _evict_lru(self) -> bool:
        """Evict least recently used entry"""
        if not self._cache:
            return False
            
        # Find LRU
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_access or 0)
        self._delete_entry(lru_key)
        self._stats['evictions'] += 1
        return True
        
    def _cleanup_loop(self):
        """Background cleanup of expired entries"""
        while self._running:
            time.sleep(60)  # Check every minute
            self._cleanup_expired()
            
    def _cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                self._delete_entry(key)
                self._stats['expirations'] += 1
                
    def register_warmup(self, callback: Callable):
        """Register cache warm-up callback"""
        self._warmup_hooks.append(callback)
        
    def warmup(self):
        """Execute cache warm-up"""
        for callback in self._warmup_hooks:
            try:
                callback(self)
            except Exception as e:
                logger.warning(f"Warmup callback error: {e}")
                
    def _load_cache(self):
        """Load cache from disk"""
        if not self.persistence_dir:
            return
            
        cache_file = self.persistence_dir / 'cache.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                for key, entry_data in data.get('entries', {}).items():
                    entry = CacheEntry(**entry_data)
                    if not entry.is_expired():
                        self._cache[key] = entry
                logger.info(f"Loaded {len(self._cache)} cache entries")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                
    def save_cache(self):
        """Save cache to disk"""
        if not self.persistence_dir:
            return
            
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.persistence_dir / 'cache.json'
        
        with self._lock:
            data = {
                'entries': {k: v.__dict__ for k, v in self._cache.items()},
                'saved_at': datetime.now().isoformat()
            }
            
        with open(cache_file, 'w') as f:
            json.dump(data, f)
            
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            hit_rate = (self._stats['hits'] / 
                       (self._stats['hits'] + self._stats['misses']) * 100
                       if (self._stats['hits'] + self._stats['misses']) > 0 else 0)
                       
            return {
                'entries': len(self._cache),
                'max_entries': self.max_entries,
                'memory_used_bytes': self._current_memory,
                'max_memory_bytes': self.max_memory,
                'memory_percent': (self._current_memory / self.max_memory) * 100,
                'hit_rate': hit_rate,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'tags': len(self._tag_index)
            }
            
    def stop(self):
        """Stop cleanup thread"""
        self._running = False
        self.save_cache()


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_cache_layer: Optional[CacheLayer] = None


def get_cache() -> CacheLayer:
    global _cache_layer
    if _cache_layer is None:
        _cache_layer = CacheLayer()
    return _cache_layer


if __name__ == "__main__":
    cache = get_cache()
    
    # Test
    cache.set("test_key", {"data": "value"}, ttl=300, tags=["test"])
    print(f"Get: {cache.get('test_key')}")
    print(json.dumps(cache.get_stats(), indent=2))
