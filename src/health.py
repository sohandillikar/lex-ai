"""
Health check utilities for lex-ai.

Verifies connectivity to PostgreSQL and OpenAI before operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class HealthStatus:
    """Result of a health check."""

    ok: bool
    message: str
    details: dict[str, str | bool | None] | None = None


def check_database() -> HealthStatus:
    """Verify PostgreSQL connection and pgvector extension."""
    try:
        from src.config import DATABASE_URL
        from src.db import get_connection, init_db

        conn = get_connection()
        init_db(conn)
        row = conn.execute("SELECT 1").fetchone()
        conn.close()
        if row and row[0] == 1:
            return HealthStatus(ok=True, message="Database connected", details={"url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "configured"})
        return HealthStatus(ok=False, message="Database check returned unexpected result")
    except Exception as e:
        return HealthStatus(ok=False, message=str(e), details={"error": str(e)})


def check_openai() -> HealthStatus:
    """Verify OpenAI API key and embedding capability."""
    from src.config import OPENAI_API_KEY

    try:
        if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
            return HealthStatus(ok=False, message="OPENAI_API_KEY is not set", details={"key_set": False})

        from src.embeddings import embed_query

        # Minimal embedding to verify API works
        _ = embed_query("health check")
        return HealthStatus(ok=True, message="OpenAI API responding", details={"key_set": True})
    except Exception as e:
        return HealthStatus(
            ok=False,
            message=str(e),
            details={"key_set": bool(OPENAI_API_KEY and OPENAI_API_KEY.strip())},
        )


def check_all() -> dict[str, HealthStatus]:
    """Run all health checks. Returns dict of component -> status."""
    return {
        "database": check_database(),
        "openai": check_openai(),
    }


def format_health_report(checks: dict[str, HealthStatus]) -> str:
    """Format health check results for display."""
    lines = ["## Health Check Report", ""]
    all_ok = True
    for name, status in checks.items():
        icon = "✓" if status.ok else "✗"
        lines.append(f"- **{name}**: {icon} {status.message}")
        if status.details:
            for k, v in status.details.items():
                lines.append(f"  - {k}: {v}")
        if not status.ok:
            all_ok = False
    lines.append("")
    lines.append("Overall: " + ("All systems operational" if all_ok else "Some checks failed"))
    return "\n".join(lines)
