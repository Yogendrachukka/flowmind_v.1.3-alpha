"""FlowMind config — load/save from ~/.flowmind.json (local) or /config/config.json (Docker)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

_DOCKER_CONFIG = Path("/config/config.json")
_LOCAL_CONFIG  = Path.home() / ".flowmind.json"


def _config_path() -> Path:
    """Return the active config path, preferring the Docker volume mount."""
    if _DOCKER_CONFIG.parent.exists():
        return _DOCKER_CONFIG
    return _LOCAL_CONFIG


CONFIG_PATH = _config_path()


def load() -> dict:
    """Return config dict, or empty dict if not yet configured."""
    path = _config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save(config: dict) -> None:
    """Write config dict to disk (mode 600)."""
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))
    path.chmod(0o600)


def get_keys(provider: str) -> list[str]:
    """Return list of API keys for *provider*."""
    config = load()
    val = config.get("providers", {}).get(provider, {}).get("keys", [])
    # legacy flat format
    if not val:
        legacy = config.get(provider, [])
        if isinstance(legacy, str):
            return [legacy] if legacy else []
        return [k for k in legacy if k]
    return [k for k in val if k]


def get_key(provider: str) -> Optional[str]:
    keys = get_keys(provider)
    return keys[0] if keys else None


def get_best_model(provider: str) -> Optional[str]:
    """Return the cached best model for *provider*, or None."""
    config = load()
    return config.get("providers", {}).get(provider, {}).get("best_model")


def get_provider_priority() -> list[str]:
    """Return ordered list of providers to try (only those with keys)."""
    config = load()
    priority = config.get("provider_priority", [])
    if priority:
        return priority
    # auto-build priority from providers that have keys
    providers_cfg = config.get("providers", {})
    active = [p for p, v in providers_cfg.items() if v.get("keys")]
    if active:
        return active
    # legacy fallback
    legacy_active = config.get("active_provider", "gemini")
    return [legacy_active]
