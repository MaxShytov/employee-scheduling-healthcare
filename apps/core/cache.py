# apps/core/cache.py
from __future__ import annotations
import hashlib
from django.conf import settings
from django.core.cache import cache

def make_params_hash(params) -> str:
    """
    Build a short stable hash of GET params.
    Accepts QueryDict or dict.
    """
    if hasattr(params, "items"):
        items = sorted((k, ",".join(v) if isinstance(v, list) else str(v))
                       for k, v in params.lists()) if hasattr(params, "lists") else \
                sorted((k, str(v)) for k, v in params.items())
    else:
        items = []
    payload = "&".join(f"{k}={v}" for k, v in items)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()[:16]

def make_key(*parts: str) -> str:
    """
    Join parts into a namespaced cache key.
    """
    ns = getattr(settings, "CACHE_NS", "app")
    cleaned = [str(p).replace(" ", "_") for p in parts if p is not None]
    return ":".join([ns, *cleaned])

def get_stats_ttl() -> int:
    return getattr(settings, "CACHE_TIMEOUTS", {}).get("stats", 300)

def get_or_set_stats(key: str, producer, ttl: int | None = None):
    """
    Fetch stats from cache or compute+store for ttl seconds.
    `producer` can be a callable with no args.
    """
    ttl = ttl or get_stats_ttl()
    val = cache.get(key)
    if val is not None:
        return val
    val = producer() if callable(producer) else producer
    cache.set(key, val, ttl)
    return val
