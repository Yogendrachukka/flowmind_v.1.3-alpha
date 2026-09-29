"""OpenRouter provider — constants, model discovery, and resolution."""

from __future__ import annotations

import logging

import httpx

PROVIDER_NAME = "openrouter"
BASE_URL      = "https://openrouter.ai/api/v1"

EXTRA_HEADERS = {
    "HTTP-Referer": "https://flowmind.local",
    "X-Title":      "FlowMind",
}

# Ranked best → fallback
_MODEL_PREFERENCE = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-70b-instruct",
    "mistralai/mistral-7b-instruct",
]

DEFAULT_MODEL = "openai/gpt-4o-mini"

logger = logging.getLogger("flowmind.providers.openrouter")


async def discover_best_model(api_key: str) -> str | None:
    """
    Query the OpenRouter /models endpoint and return the best available model,
    or None if the key is invalid.
    """
    url = f"{BASE_URL}/models"
    headers = {"Authorization": f"Bearer {api_key}", **EXTRA_HEADERS}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 401:
            return None
        if resp.status_code != 200:
            logger.warning("OpenRouter model discovery failed: HTTP %s", resp.status_code)
            return None
        data = resp.json()
        available = {m["id"] for m in data.get("data", [])}
        for preferred in _MODEL_PREFERENCE:
            if preferred in available:
                return preferred
        ids = list(available)
        return ids[0] if ids else None
    except Exception as exc:
        logger.warning("OpenRouter model discovery exception: %s", exc)
        return None


async def validate_key(api_key: str) -> bool:
    return await discover_best_model(api_key) is not None


def resolve(requested: str, best_model: str | None = None) -> str:
    if requested and requested != "default":
        lower = requested.lower()
        if "claude" in lower:
            return "anthropic/claude-3.5-sonnet"
        if "gpt" in lower:
            return "openai/gpt-4o-mini"
        if "llama" in lower:
            return "meta-llama/llama-3.1-70b-instruct"
        if "mistral" in lower:
            return "mistralai/mistral-7b-instruct"
    return best_model or DEFAULT_MODEL
