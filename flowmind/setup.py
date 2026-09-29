"""FlowMind setup wizard — interactively collect and save API keys."""

import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".flowmind.json"

PROVIDERS = ["gemini", "openrouter", "nvidia"]
PROVIDER_LABELS = {
    "gemini":     "Gemini",
    "openrouter": "OpenRouter",
    "nvidia":     "NVIDIA",
}


def run_setup() -> None:
    print("\nFlowMind Setup\n" + "─" * 30)
    print("Press Enter to skip any key you don't have yet.\n")

    existing: dict = {}
    if CONFIG_PATH.exists():
        try:
            existing = json.loads(CONFIG_PATH.read_text())
            print("Existing config found — press Enter to keep current values.\n")
        except json.JSONDecodeError:
            pass

    # ── API Keys (multi-key support) ─────────────────────────────────────────
    config: dict = {}
    for provider in PROVIDERS:
        label = PROVIDER_LABELS[provider]
        existing_keys = existing.get(provider, [])
        if isinstance(existing_keys, str):
            existing_keys = [existing_keys] if existing_keys else []

        print(f"{label} API Keys")
        print(f"  Currently set: {len(existing_keys)} key(s)")
        print("  Enter keys one at a time. Press Enter with no input to finish.")

        keys: list[str] = []
        idx = 1
        while True:
            val = input(f"  Key {idx}: ").strip()
            if not val:
                break
            keys.append(val)
            idx += 1

        # keep existing if user pressed Enter immediately
        config[provider] = keys if keys else existing_keys
        print()

    # ── Provider Priority ────────────────────────────────────────────────────
    print("Provider Priority")
    print("  Enter providers in order of preference (e.g. 1 2 3):")
    for i, p in enumerate(PROVIDERS, 1):
        n_keys = len(config[p])
        configured = f"({n_keys} key{'s' if n_keys != 1 else ''})" if n_keys else "(no keys)"
        print(f"  {i}. {PROVIDER_LABELS[p]:12s} {configured}")

    existing_priority = existing.get("provider_priority", [])
    hint = ""
    if existing_priority:
        nums = []
        for p in existing_priority:
            if p in PROVIDERS:
                nums.append(str(PROVIDERS.index(p) + 1))
        hint = f" [current: {' '.join(nums)}]"

    while True:
        raw = input(f"  Order{hint}: ").strip()
        if not raw and existing_priority:
            priority = existing_priority
            break
        try:
            indices = [int(x) - 1 for x in raw.split()]
            if all(0 <= i < len(PROVIDERS) for i in indices):
                # deduplicate while preserving order
                seen: set = set()
                priority = []
                for i in indices:
                    p = PROVIDERS[i]
                    if p not in seen:
                        priority.append(p)
                        seen.add(p)
                # append any omitted providers at the end
                for p in PROVIDERS:
                    if p not in seen:
                        priority.append(p)
                break
        except ValueError:
            pass
        print("  Invalid input — enter numbers like: 1 2 3")

    config["provider_priority"] = priority

    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    CONFIG_PATH.chmod(0o600)  # owner read/write only

    print(f"\n✓  Configuration saved to {CONFIG_PATH}")
    print(f"✓  Provider priority: {' → '.join(PROVIDER_LABELS[p] for p in priority)}")
    print("\nRun `flowmind start` to launch the gateway.\n")
