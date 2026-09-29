"""Gemini provider — constants, model discovery, and resolution."""

from __future__ import annotations

import logging

import httpx

PROVIDER_NAME = "gemini"
BASE_URL      = "https://generativelanguage.googleapis.com/v1beta/openai"

# Ranked best → fallback (used when live discovery fails)
_MODEL_PREFERENCE = [
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

DEFAULT_MODEL = _MODEL_PREFERENCE[-1]  # safest known fallback

logger = logging.getLogger("flowmind.providers.gemini")


async def discover_best_model(api_key: str) -> str | None:
    """
    Query the Gemini models endpoint and return the best available model name,
    or None if the key is invalid / the network call fails.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            logger.warning("Gemini model discovery failed: HTTP %s", resp.status_code)
            return None
        data = resp.json()
        names: list[str] = [
            m["name"].removeprefix("models/")
            for m in data.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
        for preferred in _MODEL_PREFERENCE:
            if preferred in names:
                return preferred
        # fallback: first generateContent model
        return names[0] if names else None
    except Exception as exc:
        logger.warning("Gemini model discovery exception: %s", exc)
        return None


async def validate_key(api_key: str) -> bool:
    """Return True if the key can list models (i.e. is valid)."""
    return await discover_best_model(api_key) is not None


def resolve(requested: str, best_model: str | None = None) -> str:
    if requested and requested != "default" and requested in _MODEL_PREFERENCE:
        return requested
    return best_model or _MODEL_PREFERENCE[0]
