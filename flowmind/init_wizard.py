"""FlowMind `init` wizard — zero-friction first-time setup.

Collects API keys, validates them live, discovers the best model for each
provider, and writes a ready-to-use config — no manual model names needed.
"""

from __future__ import annotations

import asyncio
import sys

import flowmind.config as cfg

_PROVIDERS = [
    ("gemini",     "Gemini",     "https://aistudio.google.com/app/apikey"),
    ("openrouter", "OpenRouter", "https://openrouter.ai/keys"),
]

_OPTIONAL_PROVIDERS = [
    ("nvidia", "NVIDIA NIM", "https://build.nvidia.com/"),
]


def run_init() -> None:
    """Entry point for `flowmind init`."""
    asyncio.run(_async_init())


async def _async_init() -> None:
    print()
    print("Welcome to FlowMind")
    print("─" * 36)
    print()

    config = cfg.load()
    providers_cfg: dict = config.get("providers", {})

    collected: list[tuple[str, str, str]] = []  # (provider, key, best_model)
    any_key_given = False

    for provider, label, key_url in _PROVIDERS:
        key = _prompt_key(label, key_url)
        if not key:
            continue
        any_key_given = True
        print(f"  Validating {label} key…", end=" ", flush=True)
        best = await _validate_and_discover(provider, key)
        if best is None:
            print("✗  Invalid key — skipped")
        else:
            print(f"✓  Ready  (model: {best})")
            collected.append((provider, key, best))

    # Optional providers
    print()
    add_nvidia = _yn("Add NVIDIA NIM key? (optional)")
    if add_nvidia:
        provider, label, key_url = _OPTIONAL_PROVIDERS[0]
        key = _prompt_key(label, key_url)
        if key:
            print(f"  Validating {label} key…", end=" ", flush=True)
            best = await _validate_and_discover(provider, key)
            if best is None:
                print("✗  Invalid key — skipped")
            else:
                print(f"✓  Ready  (model: {best})")
                collected.append((provider, key, best))

    if not collected:
        print()
        print("No valid keys entered.  Run `flowmind init` again when you have a key.")
        print("  Get a free Gemini key: https://aistudio.google.com/app/apikey")
        sys.exit(0)

    # Build new config
    new_providers: dict = {}
    priority: list[str] = []
    for provider, key, best in collected:
        new_providers[provider] = {
            "keys":       [key],
            "best_model": best,
        }
        priority.append(provider)

    # Merge with any existing providers that weren't re-entered
    for p, v in providers_cfg.items():
        if p not in new_providers and v.get("keys"):
            new_providers[p] = v
            priority.append(p)

    config["providers"]        = new_providers
    config["provider_priority"] = priority
    # Remove legacy flat keys if present
    for p in ("gemini", "openrouter", "nvidia"):
        config.pop(p, None)
    config.pop("active_provider", None)

    cfg.save(config)

    print()
    print("Done.")
    print()
    print(f"  Config: {cfg._config_path()}")
    active_labels = [label for p, label, _ in _PROVIDERS + _OPTIONAL_PROVIDERS if p in new_providers]
    for label in active_labels:
        print(f"  ✓ {label}")
    print()
    print("Run `flowmind up` to start.")
    print()


def _prompt_key(label: str, url: str) -> str:
    try:
        val = input(f"Paste {label} Key (Enter to skip):\n> ").strip()
        print()
        return val
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def _yn(prompt: str) -> bool:
    try:
        ans = input(f"{prompt} [y/N] ").strip().lower()
        print()
        return ans in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


async def _validate_and_discover(provider: str, key: str) -> str | None:
    """Validate key and return best model string, or None on failure."""
    from flowmind.providers import gemini, openrouter, nvidia
    _mods = {"gemini": gemini, "openrouter": openrouter, "nvidia": nvidia}
    mod = _mods.get(provider)
    if mod is None:
        return None
    return await mod.discover_best_model(key)
