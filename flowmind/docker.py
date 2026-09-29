"""FlowMind Docker Manager — docker compose wrapper commands.

Commands (called from cli.py):
    flowmind docker build   docker compose build
    flowmind docker start   docker compose up -d
    flowmind docker stop    docker compose down
    flowmind docker logs    docker logs -f flowmind
"""

from __future__ import annotations

import subprocess
import sys


CONTAINER_NAME = "flowmind"


def _run(cmd: list[str]) -> None:
    """Run a shell command, streaming output to the terminal."""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"✗  Command failed: {' '.join(cmd)}")
        sys.exit(exc.returncode)
    except FileNotFoundError:
        print(f"✗  Command not found: {cmd[0]}")
        print("   Make sure Docker is installed and in your PATH.")
        sys.exit(1)


def build() -> None:
    """Build the FlowMind Docker image."""
    print("Building FlowMind Docker image...")
    _run(["docker", "compose", "build"])
    print("✓  Build complete")


def start() -> None:
    """Start FlowMind via Docker Compose (detached)."""
    print("Starting FlowMind container...")
    _run(["docker", "compose", "up", "-d"])
    print("✓  FlowMind is running at http://localhost:4000")
    print("   Health check: curl http://localhost:4000/health")


def stop() -> None:
    """Stop the FlowMind Docker container."""
    print("Stopping FlowMind container...")
    _run(["docker", "compose", "down"])
    print("✓  FlowMind stopped")


def logs() -> None:
    """Follow the FlowMind container logs (Ctrl+C to exit)."""
    print(f"Following logs for container '{CONTAINER_NAME}' (Ctrl+C to exit)...\n")
    _run(["docker", "logs", "-f", CONTAINER_NAME])
