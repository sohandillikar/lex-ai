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


def _docker_is_running() -> bool:
    """Return True if Docker daemon is responsive."""
    result = subprocess.run(
        ["docker", "info"],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )
    return result.returncode == 0


def _start_docker_desktop() -> bool:
    """Attempt to start Docker Desktop. Returns True if launch was attempted."""
    if sys.platform == "win32":
        paths = [
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Docker" / "Docker" / "Docker Desktop.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Docker" / "Docker Desktop.exe",
        ]
        for exe in paths:
            if exe.exists():
                log(f"Starting Docker Desktop ({exe})...")
                subprocess.Popen(
                    [str(exe)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
    elif sys.platform == "darwin":
        docker_app = Path("/Applications/Docker.app")
        if docker_app.exists():
            log("Starting Docker Desktop...")
            subprocess.Popen(
                ["open", "-a", "Docker"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
    return False


def _wait_for_docker(timeout: int = 90) -> bool:
    """Wait for Docker daemon to become ready. Returns True if ready."""
    log("Waiting for Docker to start...")
    start = time.time()
    while (time.time() - start) < timeout:
        if _docker_is_running():
            return True
        time.sleep(3)
    return False


def check_docker() -> None:
    """Ensure Docker is installed and available. Start Docker Desktop if needed."""
    if not shutil.which("docker"):
        log("Error: docker not found. Please install Docker Desktop first.")
        sys.exit(1)

    if _docker_is_running():
        return

    log("Docker is not running.")
    if _start_docker_desktop():
        if not _wait_for_docker():
            log("Error: Docker did not start in time. Please start Docker Desktop manually and run setup again.")
            sys.exit(1)
    else:
        log("Error: Please start Docker Desktop manually and run setup again.")
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


def ensure_lex_ai_database() -> None:
    """Ensure the lex_ai database exists (handles reused volumes from older setups)."""
    log("Ensuring lex_ai database exists...")
    result = subprocess.run(
        [
            "docker", "compose", "exec", "-T", "postgres",
            "psql", "-U", "postgres", "-d", "postgres",
            "-c", "CREATE DATABASE lex_ai;",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )
    out = (result.stderr or b"") + (result.stdout or b"")
    if result.returncode == 0:
        log("Database lex_ai ready.")
    elif b"already exists" in out:
        log("Database lex_ai already exists.")
    else:
        log("Error: Could not create lex_ai database. Try: docker compose down -v && docker compose up -d")
        log("Then run setup again.")
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
    ensure_lex_ai_database()

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
