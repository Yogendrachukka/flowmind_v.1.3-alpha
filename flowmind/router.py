"""FlowMind Router — resolves models and delegates to the failover engine."""

from __future__ import annotations

from typing import Any

import flowmind.config as cfg
from flowmind.failover import call_with_failover
from flowmind.providers import gemini, openrouter, nvidia

_PROVIDER_MODULES = {
    "gemini":     gemini,
    "openrouter": openrouter,
    "nvidia":     nvidia,
}


async def route(model: str, messages: list[dict], temperature: float, max_tokens: int, extra_fields: dict[str, Any] = None) -> dict[str, Any]:
    """
    Build the outbound payload and call the failover engine.

    Model resolution uses the cached best_model from `flowmind init` so users
    never need to specify model names.
    """
    payload: dict[str, Any] = {
        "model":       model,  # The original requested model, to be resolved per-provider in failover
        "messages":    messages,
        "temperature": temperature,
        "max_tokens":  max_tokens,
    }

    if extra_fields:
        payload.update(extra_fields)

    return await call_with_failover(payload)
