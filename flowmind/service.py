"""FlowMind Service Manager — systemd integration.

Commands (called from cli.py):
    flowmind service install   Write /etc/systemd/system/flowmind.service
    flowmind service start     systemctl start flowmind
    flowmind service stop      systemctl stop flowmind
    flowmind service status    Pretty-print service status
    flowmind daemon            Start in foreground (no systemd)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

SERVICE_NAME = "flowmind"
SERVICE_PATH = Path("/etc/systemd/system/flowmind.service")


def _flowmind_bin() -> str:
    """Return the absolute path to the flowmind executable."""
    exe = shutil.which("flowmind")
    if exe:
        return exe
    # Fallback: same interpreter running us
    return f"{sys.executable} -m flowmind"


def _python_bin() -> str:
    return sys.executable


def _service_unit() -> str:
    exe = _flowmind_bin()
    user = os.environ.get("USER", "root")
    return f"""\
[Unit]
Description=FlowMind Local AI Gateway
After=network.target
Wants=network.target

[Service]
Type=simple
User={user}
ExecStart={exe} daemon
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=flowmind

[Install]
WantedBy=multi-user.target
"""


def install() -> None:
    """Write the systemd unit file and enable the service."""
    if os.geteuid() != 0:
        print("✗  flowmind service install requires sudo / root.")
        print("   Run: sudo flowmind service install")
        sys.exit(1)

    unit = _service_unit()
    SERVICE_PATH.write_text(unit)
    print(f"✓  Unit file written to {SERVICE_PATH}")

    _run(["systemctl", "daemon-reload"])
    _run(["systemctl", "enable", SERVICE_NAME])
    print("✓  Service enabled (will start on boot)")
    print()
    print("To start now:")
    print("  sudo flowmind service start")


def start() -> None:
    if os.geteuid() != 0:
        print("✗  Requires sudo.  Run: sudo flowmind service start")
        sys.exit(1)
    _run(["systemctl", "start", SERVICE_NAME])
    print(f"✓  {SERVICE_NAME} started")
    status()


def stop() -> None:
    if os.geteuid() != 0:
        print("✗  Requires sudo.  Run: sudo flowmind service stop")
        sys.exit(1)
    _run(["systemctl", "stop", SERVICE_NAME])
    print(f"✓  {SERVICE_NAME} stopped")


def status() -> None:
    """Pretty-print service status (works without root)."""
    import flowmind.config as cfg
    from flowmind import __version__

    # Try systemctl is-active
    try:
        result = subprocess.run(
            ["systemctl", "is-active", SERVICE_NAME],
            capture_output=True, text=True
        )
        state = result.stdout.strip()
    except FileNotFoundError:
        state = "unknown (systemctl not found)"

    icon = "●" if state == "active" else "○"
    print(f"\nFlowMind Service")
    print("─" * 30)
    print(f"Status  : {icon} {state}")
    print(f"Port    : 4000")
    print(f"Version : {__version__}")
    print()

    priority = cfg.get_provider_priority()
    print("Providers:")
    for p in ["gemini", "openrouter", "nvidia"]:
        keys = cfg.get_keys(p)
        rank_marker = "✓" if p in priority and keys else ("–" if keys else " ")
        label = p.capitalize()
        key_info = f"{len(keys)} key{'s' if len(keys) != 1 else ''}" if keys else "no keys"
        print(f"  {rank_marker} {label:12s} {key_info}")
    print()


def uninstall() -> None:
    if os.geteuid() != 0:
        print("✗  Requires sudo.  Run: sudo flowmind service uninstall")
        sys.exit(1)
    _run(["systemctl", "stop", SERVICE_NAME], check=False)
    _run(["systemctl", "disable", SERVICE_NAME], check=False)
    if SERVICE_PATH.exists():
        SERVICE_PATH.unlink()
        print(f"✓  Removed {SERVICE_PATH}")
    _run(["systemctl", "daemon-reload"])
    print("✓  Service uninstalled")


def _run(cmd: list[str], check: bool = True) -> None:
    try:
        subprocess.run(cmd, check=check)
    except subprocess.CalledProcessError as exc:
        print(f"✗  Command failed: {' '.join(cmd)}")
        if check:
            sys.exit(exc.returncode)
    except FileNotFoundError:
        print(f"✗  systemctl not found — is systemd running on this machine?")
        if check:
            sys.exit(1)
