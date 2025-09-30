"""
Aggressive caching system for 2-category transformations.
Implements TTL-based caches for OPA, SBOM, and LLM responses.
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from threading import Lock


@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata."""

    value: Any
    timestamp: float
    ttl_seconds: float
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl_seconds

    def is_valid(self) -> bool:
        """Check if cache entry is valid (not expired)."""
        return not self.is_expired()


class AggressiveCache:
    """Aggressive cache with TTL and size limits."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}

    def _make_key(self, prefix: str, data: Any) -> str:
        """Create cache key from prefix and data."""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        else:
            data_str = str(data)

        content_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return f"{prefix}:{content_hash}"

    def get(self, prefix: str, data: Any) -> Optional[Any]:
        """Get value from cache."""
        key = self._make_key(prefix, data)

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_valid():
                    entry.hit_count += 1
                    self._stats["hits"] += 1
                    return entry.value
                else:
                    # Expired entry
                    del self._cache[key]
                    self._stats["expired"] += 1

            self._stats["misses"] += 1
            return None

    def set(self, prefix: str, data: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache."""
        key = self._make_key(prefix, data)
        ttl = ttl or self.default_ttl

        with self._lock:
            # Evict if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            self._cache[key] = CacheEntry(value=value, timestamp=time.time(), ttl_seconds=ttl)

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find entry with lowest hit_count
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].hit_count)
        del self._cache[lru_key]
        self._stats["evictions"] += 1

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate,
                **self._stats,
            }

    def warmup(self, warmup_data: Dict[str, Any]) -> None:
        """Warm up cache with pre-computed data."""
        for prefix, entries in warmup_data.items():
            for data, value in entries.items():
                self.set(prefix, data, value, ttl=7200.0)  # 2 hours for warmup


class CacheManager:
    """Global cache manager for all components."""

    def __init__(self):
        self.opa_cache = AggressiveCache(max_size=500, default_ttl=1800.0)  # 30 min
        self.sbom_cache = AggressiveCache(max_size=200, default_ttl=3600.0)  # 1 hour
        self.llm_cache = AggressiveCache(max_size=1000, default_ttl=3600.0)  # 1 hour
        self.metrics_cache = AggressiveCache(max_size=100, default_ttl=600.0)  # 10 min

    def get_opa_result(self, policy: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get OPA result from cache."""
        return self.opa_cache.get("opa", {"policy": policy, "input": input_data})

    def set_opa_result(
        self, policy: str, input_data: Dict[str, Any], result: Dict[str, Any]
    ) -> None:
        """Set OPA result in cache."""
        self.opa_cache.set("opa", {"policy": policy, "input": input_data}, result)

    def get_sbom_result(self, package: str, version: str) -> Optional[Dict[str, Any]]:
        """Get SBOM result from cache."""
        return self.sbom_cache.get("sbom", {"package": package, "version": version})

    def set_sbom_result(self, package: str, version: str, result: Dict[str, Any]) -> None:
        """Set SBOM result in cache."""
        self.sbom_cache.set("sbom", {"package": package, "version": version}, result)

    def get_llm_result(
        self, prompt: str, model: str, temperature: float
    ) -> Optional[Dict[str, Any]]:
        """Get LLM result from cache."""
        return self.llm_cache.get("llm", {"prompt": prompt, "model": model, "temp": temperature})

    def set_llm_result(
        self, prompt: str, model: str, temperature: float, result: Dict[str, Any]
    ) -> None:
        """Set LLM result in cache."""
        self.llm_cache.set("llm", {"prompt": prompt, "model": model, "temp": temperature}, result)

    def get_metrics(self, case_id: str, mode: str) -> Optional[Dict[str, Any]]:
        """Get metrics from cache."""
        return self.metrics_cache.get("metrics", {"case_id": case_id, "mode": mode})

    def set_metrics(self, case_id: str, mode: str, metrics: Dict[str, Any]) -> None:
        """Set metrics in cache."""
        self.metrics_cache.set("metrics", {"case_id": case_id, "mode": mode}, metrics)

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        return {
            "opa": self.opa_cache.get_stats(),
            "sbom": self.sbom_cache.get_stats(),
            "llm": self.llm_cache.get_stats(),
            "metrics": self.metrics_cache.get_stats(),
        }

    def clear_all(self) -> None:
        """Clear all caches."""
        self.opa_cache.clear()
        self.sbom_cache.clear()
        self.llm_cache.clear()
        self.metrics_cache.clear()

    def warmup_from_file(self, warmup_file: str) -> None:
        """Warm up caches from file."""
        if Path(warmup_file).exists():
            with open(warmup_file) as f:
                warmup_data = json.load(f)

            self.opa_cache.warmup(warmup_data.get("opa", {}))
            self.sbom_cache.warmup(warmup_data.get("sbom", {}))
            self.llm_cache.warmup(warmup_data.get("llm", {}))


# Global cache manager instance
cache_manager = CacheManager()
