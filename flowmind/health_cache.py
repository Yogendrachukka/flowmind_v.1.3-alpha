"""FlowMind Provider Health Cache.

Tracks per-provider failure state so the router can skip providers that
recently failed, avoiding wasted HTTP round-trips.

Usage:
    from flowmind.health_cache import mark_failed, mark_healthy, is_available

The cache is in-process only (not persisted to disk) and is intentionally
simple: a provider is considered unavailable for COOLDOWN_SECONDS after its
last failure.  A successful response clears the failure immediately.
"""

from __future__ import annotations

import time
from threading import Lock
from typing import Dict, Optional

# Seconds a provider stays "cooled down" after a failure before we retry it.
COOLDOWN_SECONDS: int = 30

_lock = Lock()

# provider_name -> timestamp of last failure (None = healthy / never failed)
_last_failure: Dict[str, Optional[float]] = {}
# provider_name -> human-readable last error
_last_error: Dict[str, Optional[str]] = {}


def mark_failed(provider: str, reason: str = "") -> None:
    """Record that *provider* just failed."""
    with _lock:
        _last_failure[provider] = time.monotonic()
        _last_error[provider] = reason


def mark_healthy(provider: str) -> None:
    """Record that *provider* just responded successfully."""
    with _lock:
        _last_failure[provider] = None
        _last_error[provider] = None


def is_available(provider: str) -> bool:
    """Return True if *provider* should be tried right now."""
    with _lock:
        ts = _last_failure.get(provider)
        if ts is None:
            return True
        elapsed = time.monotonic() - ts
        return elapsed >= COOLDOWN_SECONDS


def snapshot() -> dict:
    """Return a read-only snapshot of current health state (for /health endpoint)."""
    now = time.monotonic()
    with _lock:
        result = {}
        for provider, ts in _last_failure.items():
            if ts is None:
                result[provider] = {"status": "healthy", "last_error": None}
            else:
                elapsed = now - ts
                remaining = max(0.0, COOLDOWN_SECONDS - elapsed)
                result[provider] = {
                    "status": "cooling_down" if remaining > 0 else "available",
                    "last_error": _last_error.get(provider),
                    "cooldown_remaining_s": round(remaining, 1),
                }
    return result
