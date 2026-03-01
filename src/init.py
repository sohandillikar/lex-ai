"""
MCP server configuration wizard for lex-ai.

Registers the lex-ai MCP server with Cursor or Claude Code.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

from dotenv import dotenv_values

from src.config import PROJECT_ROOT, SERVER_NAME

logger = logging.getLogger(__name__)


def _load_env() -> dict[str, str]:
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        print(f"Error: .env file not found at {env_file}")
        print("Copy .env.example to .env and fill in your values first.")
        sys.exit(1)

    values = dotenv_values(env_file)
    missing = [k for k in ("DATABASE_URL", "OPENAI_API_KEY") if not values.get(k)]
    if missing:
        print(f"Error: missing required variables in .env: {', '.join(missing)}")
        sys.exit(1)

    return values


def _detect_python() -> str:
    python_path = shutil.which("python3")
    if not python_path:
        python_path = shutil.which("python")
    if not python_path:
        print("Error: could not find python3 or python on PATH.")
        sys.exit(1)
    return python_path


def _build_server_config(env: dict[str, str], python_path: str) -> dict:
    cwd = str(PROJECT_ROOT)
    return {
        "command": python_path,
        "args": ["-m", "src.server"],
        "cwd": cwd,
        "env": {
            "PYTHONPATH": cwd,
            "DATABASE_URL": env["DATABASE_URL"],
            "OPENAI_API_KEY": env["OPENAI_API_KEY"],
        },
    }


def _read_config(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"mcpServers": {}}


def _write_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n")


def _init_db() -> None:
    from src.db import get_connection, init_db

    max_attempts = 5
    delay_seconds = 2
    for attempt in range(1, max_attempts + 1):
        try:
            conn = get_connection()
            init_db(conn)
            conn.close()
            print("Database tables initialized.")
            return
        except Exception as e:
            if attempt == max_attempts:
                print("Could not connect to PostgreSQL. Is the database running?")
                print(f"Error: {e}")
                sys.exit(1)
            time.sleep(delay_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure the lex-ai MCP server for Cursor or Claude Code",
    )
    parser.add_argument(
        "--cursor",
        action="store_true",
        help="Configure for Cursor (writes to ~/.cursor/mcp.json)",
    )
    parser.add_argument(
        "--claude",
        action="store_true",
        help="Configure for Claude Code (writes to .mcp.json in project)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-essential output",
    )
    args = parser.parse_args()

    if not args.quiet:
        print("=" * 50)
        print("  Documentation MCP — Setup")
        print("=" * 50)

    env = _load_env()
    for k, v in env.items():
        os.environ[k] = str(v) if v else os.environ.get(k, "")

    _init_db()

    python_path = _detect_python()

    if not args.quiet:
        print(f"\nDetected python: {python_path}")
        print(f"Project root:    {PROJECT_ROOT}\n")

    config_path: Path
    if args.cursor:
        config_path = Path.home() / ".cursor" / "mcp.json"
    elif args.claude:
        config_path = PROJECT_ROOT / ".mcp.json"
    else:
        print("Which client are you configuring?")
        print("  1. Cursor")
        print("  2. Claude Code")

        choice = input("\nEnter 1 or 2: ").strip()
        if choice == "1":
            config_path = Path.home() / ".cursor" / "mcp.json"
        elif choice == "2":
            config_path = PROJECT_ROOT / ".mcp.json"
        else:
            print("Invalid choice. Exiting.")
            sys.exit(1)

    config = _read_config(config_path)
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    server_config = _build_server_config(env, python_path)
    action = "Updated" if SERVER_NAME in config["mcpServers"] else "Added"
    config["mcpServers"][SERVER_NAME] = server_config

    _write_config(config_path, config)
    if not args.quiet:
        print(f"\n{action} '{SERVER_NAME}' in {config_path}")
        print("Restart your client to pick up the new MCP server.")


if __name__ == "__main__":
    main()
