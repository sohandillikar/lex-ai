#!/usr/bin/env python3
"""
Cross-platform setup script for lex-ai.
Runs on Windows, macOS, and Linux.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def log(msg: str) -> None:
    print(msg, flush=True)


def check_python() -> None:
    """Ensure Python 3.11+ is available."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        log(f"Error: Python 3.11+ required. Found {version.major}.{version.minor}")
        sys.exit(1)


def check_docker() -> None:
    """Ensure Docker is installed and available."""
    docker = shutil.which("docker")
    if not docker:
        log("Error: docker not found. Please install Docker first.")
        sys.exit(1)


def ensure_env() -> None:
    """Copy .env.example to .env if .env does not exist."""
    env_file = PROJECT_ROOT / ".env"
    example = PROJECT_ROOT / ".env.example"
    if not env_file.exists():
        if not example.exists():
            log("Error: .env.example not found. Cannot create .env.")
            sys.exit(1)
        shutil.copy(example, env_file)
        log("Created .env from .env.example. Please edit .env and add your OpenAI API key.")
    else:
        log(".env already exists.")


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, optionally from a given directory."""
    log(f"Running: {' '.join(str(x) for x in cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        check=check,
    )


def docker_compose(args: list[str]) -> None:
    """Run docker compose with the given arguments."""
    run(["docker", "compose"] + args)


def pip_install(requirements: str) -> None:
    """Install Python dependencies."""
    run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", requirements],
    )


def crawl4ai_setup() -> None:
    """Install Playwright browsers for Crawl4AI."""
    # Try crawl4ai-setup from PATH first (works when Scripts/bin is on PATH)
    which = shutil.which("crawl4ai-setup")
    if which:
        run([which])
        return

    # Try explicit path next to Python executable
    exe = Path(sys.executable)
    if sys.platform == "win32":
        setup_cmd = exe.parent / "Scripts" / "crawl4ai-setup.exe"
    else:
        setup_cmd = exe.parent / "crawl4ai-setup"
    if setup_cmd.exists():
        run([str(setup_cmd)])
        return

    # pip run executes installed console scripts (cross-platform)
    result = subprocess.run(
        [sys.executable, "-m", "pip", "run", "crawl4ai-setup"],
        cwd=PROJECT_ROOT,
    )
    if result.returncode == 0:
        return

    # Fallback: playwright install (crawl4ai-setup primarily runs this)
    log("Running playwright install chromium...")
    run([sys.executable, "-m", "playwright", "install", "chromium"])


def wait_for_postgres() -> None:
    """Wait until PostgreSQL is ready."""
    log("Waiting for PostgreSQL to be ready...")
    max_attempts = 30
    for i in range(max_attempts):
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres", "pg_isready", "-U", "postgres"],
            cwd=PROJECT_ROOT,
            capture_output=True,
        )
        if result.returncode == 0:
            log("PostgreSQL is ready.")
            return
        if i < max_attempts - 1:
            time.sleep(2)
    log("Error: PostgreSQL did not become ready in time.")
    sys.exit(1)


def main() -> None:
    check_python()
    check_docker()
    ensure_env()

    log("Starting PostgreSQL + pgvector...")
    docker_compose(["up", "-d"])

    log("Installing dependencies...")
    pip_install(str(PROJECT_ROOT / "requirements.txt"))

    log("Installing Playwright browsers for Crawl4AI...")
    crawl4ai_setup()

    wait_for_postgres()

    log("Setting up MCP server...")
    client = os.environ.get("LEX_AI_MCP_CLIENT", "").lower()
    init_args = [sys.executable, "-m", "src.init"]
    if client == "cursor":
        init_args.append("--cursor")
    elif client == "claude":
        init_args.append("--claude")
    run(init_args, cwd=PROJECT_ROOT)

    log("\nSetup complete!")


if __name__ == "__main__":
    main()
