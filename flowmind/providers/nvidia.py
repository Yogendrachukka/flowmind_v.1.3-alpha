"""NVIDIA NIM provider — constants, model discovery, and resolution."""

from __future__ import annotations

import logging

import httpx

PROVIDER_NAME = "nvidia"
BASE_URL      = "https://integrate.api.nvidia.com/v1"

_MODEL_PREFERENCE = [
    "meta/llama-3.1-405b-instruct",
    "meta/llama-3.1-70b-instruct",
    "mistralai/mixtral-8x22b-instruct-v0.1",
    "mistralai/mistral-7b-instruct-v0.3",
]

DEFAULT_MODEL = _MODEL_PREFERENCE[-1]

logger = logging.getLogger("flowmind.providers.nvidia")


async def discover_best_model(api_key: str) -> str | None:
    url = f"{BASE_URL}/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 401:
            return None
        if resp.status_code != 200:
            logger.warning("NVIDIA model discovery failed: HTTP %s", resp.status_code)
            return None
        data = resp.json()
        available = {m["id"] for m in data.get("data", [])}
        for preferred in _MODEL_PREFERENCE:
            if preferred in available:
                return preferred
        ids = list(available)
        return ids[0] if ids else None
    except Exception as exc:
        logger.warning("NVIDIA model discovery exception: %s", exc)
        return None


async def validate_key(api_key: str) -> bool:
    return await discover_best_model(api_key) is not None


def resolve(requested: str, best_model: str | None = None) -> str:
    if requested and requested != "default" and requested in _MODEL_PREFERENCE:
        return requested
    return best_model or DEFAULT_MODEL
