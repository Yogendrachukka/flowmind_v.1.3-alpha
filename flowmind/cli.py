"""FlowMind CLI — entry point for the `flowmind` command."""

import sys


HELP = """\
FlowMind v0.2.0

Commands:
  flowmind init               Set up API keys and auto-detect models
  flowmind up                 Start FlowMind (Docker preferred, local fallback)
  flowmind status             Show provider health and active configuration

Advanced:
  flowmind doctor             Detailed config and connectivity check
  flowmind providers          List configured providers and discovered models
  flowmind logs               Follow service logs

Legacy (still supported):
  flowmind setup              Interactive setup (multi-key, manual priority)
  flowmind start              Start gateway in foreground (local Python)
  flowmind daemon             Start as background-compatible foreground process

Docker subcommands:
  flowmind docker build / start / stop / logs
"""


def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    # ── docker subcommand ────────────────────────────────────────────────
    if cmd == "docker":
        subcmd = args[1] if len(args) > 1 else "help"
        from flowmind import docker as dkr
        dispatch = {
            "build": dkr.build,
            "start": dkr.start,
            "stop":  dkr.stop,
            "logs":  dkr.logs,
        }
        fn = dispatch.get(subcmd)
        if fn:
            fn()
        else:
            print(f"Unknown docker subcommand: {subcmd!r}")
            print("Available: build, start, stop, logs")
            sys.exit(1)
        return

    # ── service subcommand (legacy) ──────────────────────────────────────
    if cmd == "service":
        subcmd = args[1] if len(args) > 1 else "status"
        from flowmind import service as svc
        dispatch = {
            "install":   svc.install,
            "start":     svc.start,
            "stop":      svc.stop,
            "status":    svc.status,
            "uninstall": svc.uninstall,
        }
        fn = dispatch.get(subcmd)
        if fn:
            fn()
        else:
            print(f"Unknown service subcommand: {subcmd!r}")
            print("Available: install, start, stop, status, uninstall")
            sys.exit(1)
        return

    # ── init (v0.2 zero-friction wizard) ────────────────────────────────
    if cmd == "init":
        from flowmind.init_wizard import run_init
        run_init()
        return

    # ── up (Docker-first start) ──────────────────────────────────────────
    if cmd == "up":
        _up()
        return

    # ── status ───────────────────────────────────────────────────────────
    if cmd == "status":
        _status()
        return

    # ── providers ────────────────────────────────────────────────────────
    if cmd == "providers":
        _providers()
        return

    # ── logs ─────────────────────────────────────────────────────────────
    if cmd == "logs":
        import shutil, subprocess
        if shutil.which("docker"):
            subprocess.run(["docker", "logs", "-f", "flowmind"])
        else:
            print("Docker not available. For local installs, check your terminal output.")
        return

    # ── daemon ───────────────────────────────────────────────────────────
    if cmd == "daemon":
        from flowmind.server import start_server
        start_server(daemon=True)
        return

    # ── legacy setup ─────────────────────────────────────────────────────
    if cmd == "setup":
        from flowmind.setup import run_setup
        run_setup()
        return

    # ── legacy start ─────────────────────────────────────────────────────
    if cmd == "start":
        from flowmind.server import start_server
        start_server()
        return

    # ── doctor ───────────────────────────────────────────────────────────
    if cmd == "doctor":
        _doctor()
        return

    # ── version ──────────────────────────────────────────────────────────
    if cmd in ("version", "--version", "-v"):
        from flowmind import __version__
        print(f"flowmind {__version__}")
        return

    print(HELP)


# ── `flowmind up` ────────────────────────────────────────────────────────────

def _up() -> None:
    """Start FlowMind. Prefers Docker; falls back to local Python server."""
    import shutil
    import flowmind.config as cfg
    from flowmind import __version__

    config = cfg.load()
    if not config or not config.get("providers"):
        # check legacy format too
        if not any(config.get(p) for p in ("gemini", "openrouter", "nvidia")):
            print("No configuration found. Run `flowmind init` first.")
            return

    priority = cfg.get_provider_priority()

    if shutil.which("docker"):
        print("FlowMind Running\n")
        print("URL:")
        print("  http://localhost:4000\n")
        print("Providers:")
        for p in priority:
            print(f"  ✓ {p.capitalize()}")
        print()
        print("Failover:")
        print("  Enabled\n")
        from flowmind.docker import start
        start()
    else:
        print("Docker not found — starting local Python server.\n")
        from flowmind.server import start_server
        start_server()


# ── `flowmind status` ────────────────────────────────────────────────────────

def _status() -> None:
    """Show active providers, discovered models, and service health."""
    import flowmind.config as cfg

    config = cfg.load()
    if not config:
        print("Not configured. Run `flowmind init` first.")
        return

    priority = cfg.get_provider_priority()
    providers_cfg = config.get("providers", {})

    print("FlowMind Status\n" + "─" * 36)
    print(f"Config: {cfg._config_path()}\n")

    for p in priority:
        keys = cfg.get_keys(p)
        best = cfg.get_best_model(p) or "(unknown)"
        n = len(keys)
        label = p.capitalize()
        status = f"✓  {label:12s}  {n} key{'s' if n != 1 else ''}  →  {best}"
        print(status)

    unconfigured = [p for p in ("gemini", "openrouter", "nvidia") if p not in priority]
    for p in unconfigured:
        print(f"–  {p.capitalize():12s}  not configured")

    print()

    # Check if service is reachable
    import urllib.request, urllib.error
    try:
        with urllib.request.urlopen("http://localhost:4000/health", timeout=2) as r:
            import json
            data = json.loads(r.read())
            print(f"Service: running  (v{data.get('version', '?')}) at http://localhost:4000")
    except Exception:
        print("Service: not running  (run `flowmind up`)")

    print("─" * 36)


# ── `flowmind providers` ─────────────────────────────────────────────────────

def _providers() -> None:
    """List all configured providers with their discovered models."""
    import flowmind.config as cfg

    config = cfg.load()
    if not config:
        print("Not configured. Run `flowmind init` first.")
        return

    priority = cfg.get_provider_priority()
    providers_cfg = config.get("providers", {})

    print("Providers\n" + "─" * 36)
    for i, p in enumerate(priority, 1):
        keys = cfg.get_keys(p)
        best = cfg.get_best_model(p) or "auto"
        print(f"  {i}. {p.capitalize():12s}  {len(keys)} key(s)  model: {best}")
    print()


# ── `flowmind doctor` ────────────────────────────────────────────────────────

def _doctor() -> None:
    """Detailed health-check: config, keys, models, Docker, systemd."""
    import json, shutil, subprocess
    import flowmind.config as cfg

    config_path = cfg._config_path()
    print("FlowMind Doctor\n" + "─" * 36)
    print(f"Config path: {config_path}")

    if not config_path.exists():
        print("✗  Config file not found — run `flowmind init` first")
        print("─" * 36)
        print("Issues found — see above.")
        return

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        print("✗  Config file is not valid JSON")
        print("─" * 36)
        print("Issues found — see above.")
        return

    # Providers
    providers_cfg = config.get("providers", {})
    for provider in ("gemini", "openrouter", "nvidia"):
        keys = cfg.get_keys(provider)
        best = cfg.get_best_model(provider)
        n = len(keys)
        if n:
            model_str = f"  model → {best}" if best else "  (run `flowmind init` to detect model)"
            print(f"✓  {provider:12s} {n} key{'s' if n > 1 else ''}{model_str}")
        else:
            print(f"–  {provider:12s} no keys set  (optional)")

    # Priority
    priority = cfg.get_provider_priority()
    if priority:
        print(f"✓  provider_priority: {' → '.join(priority)}")
    else:
        print("–  provider_priority not set — run `flowmind init`")

    # Docker
    if shutil.which("docker"):
        result = subprocess.run(
            ["docker", "inspect", "--format={{.State.Status}}", "flowmind"],
            capture_output=True, text=True
        )
        state = result.stdout.strip()
        if state == "running":
            print("✓  Docker container: running")
        elif state:
            print(f"–  Docker container: {state}")
        else:
            print("–  Docker container: not found (run `flowmind up`)")
    else:
        print("–  Docker not available on this system")

    # Systemd
    if shutil.which("systemctl"):
        result = subprocess.run(
            ["systemctl", "is-active", "flowmind"],
            capture_output=True, text=True
        )
        state = result.stdout.strip()
        if state == "active":
            print("✓  systemd service: running")
        elif state == "inactive":
            print("–  systemd service: installed but not running")
        else:
            print(f"–  systemd service: {state}")
    else:
        print("–  systemd not available on this system")

    print("─" * 36)
    print("Doctor complete ✓")
