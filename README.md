# FlowMind

**Uninterrupted AI Workflows.**

Local AI gateway with automatic provider failover. One URL, multiple providers, zero downtime.

---

## Install

```bash
pipx install flowmind
```

Or with pip:

```bash
pip install flowmind
```

---

## Get started in three commands

### 1. Init

```bash
flowmind init
```

```
Welcome to FlowMind
────────────────────────────────────

Paste Gemini Key (Enter to skip):
>

  Validating Gemini key… ✓  Ready  (model: gemini-2.0-flash)

Paste OpenRouter Key (Enter to skip):
>

  Validating OpenRouter key… ✓  Ready  (model: anthropic/claude-3.5-sonnet)

Done.
  Config: ~/.flowmind.json
  ✓ Gemini
  ✓ OpenRouter

Run `flowmind up` to start.
```

FlowMind validates your keys, discovers the best available model for each provider, and builds the configuration automatically. No model names to look up.

### 2. Up

```bash
flowmind up
```

```
FlowMind Running

URL:
  http://localhost:4000

Providers:
  ✓ Gemini
  ✓ OpenRouter

Failover:
  Enabled
```

### 3. Use

Point any OpenAI-compatible client at `http://localhost:4000`:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

Or use the Anthropic-compatible endpoint:

```bash
curl http://localhost:4000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

---

## How it works

**Failover** — FlowMind tries providers in your configured priority order. If Gemini returns a 429 or goes down, requests automatically continue through OpenRouter or NVIDIA NIM. No intervention needed.

**Auto model selection** — `flowmind init` queries each provider's API to find the best model your key has access to. The result is cached in your config. You never specify model names.

**Health cache** — failed providers enter a 30-second cooldown before being retried, avoiding wasted round-trips.

---

## Commands

| Command | What it does |
|---|---|
| `flowmind init` | Validate keys, discover models, write config |
| `flowmind up` | Start (Docker preferred, local Python fallback) |
| `flowmind status` | Show providers, models, and service health |
| `flowmind doctor` | Detailed config + connectivity check |
| `flowmind providers` | List configured providers and discovered models |
| `flowmind logs` | Follow service logs |

---

## Configuration

Config is stored at `~/.flowmind.json` (or `/config/config.json` inside Docker).

```json
{
  "providers": {
    "gemini": {
      "keys": ["AIza..."],
      "best_model": "gemini-2.0-flash"
    },
    "openrouter": {
      "keys": ["sk-or-..."],
      "best_model": "anthropic/claude-3.5-sonnet"
    }
  },
  "provider_priority": ["gemini", "openrouter"]
}
```

You never need to edit this by hand. Re-run `flowmind init` to update it.

---

## Docker

`flowmind up` uses Docker Compose internally when Docker is available. The config directory is mounted automatically.

To manage Docker directly:

```bash
flowmind docker build
flowmind docker start
flowmind docker stop
flowmind docker logs
```

---

## Supported providers

| Provider | Keys | Models |
|---|---|---|
| [Gemini](https://aistudio.google.com/app/apikey) | Free tier available | Auto-detected |
| [OpenRouter](https://openrouter.ai/keys) | Pay-per-use | Auto-detected |
| [NVIDIA NIM](https://build.nvidia.com/) | Free tier available | Auto-detected |

---

## License

MIT
# flowmind_v.1.3-alpha
