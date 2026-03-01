"""
Tests for src.health.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.health import HealthStatus, check_all, check_database, check_openai, format_health_report


class TestHealthStatus:
    def test_dataclass_fields(self):
        s = HealthStatus(ok=True, message="OK", details={"key": "value"})
        assert s.ok is True
        assert s.message == "OK"
        assert s.details == {"key": "value"}


class TestCheckDatabase:
    @pytest.mark.skip(reason="Requires running PostgreSQL")
    def test_check_database_integration(self):
        status = check_database()
        assert status.ok is True

    def test_check_database_failure(self):
        with patch("src.health.get_connection") as mock:
            mock.side_effect = Exception("Connection refused")
            status = check_database()
            assert status.ok is False
            assert "Connection" in status.message or "refused" in status.message


class TestCheckOpenai:
    def test_returns_health_status(self):
        """check_openai always returns a HealthStatus (may fail if no API key)."""
        status = check_openai()
        assert isinstance(status, HealthStatus)
        assert hasattr(status, "ok")
        assert hasattr(status, "message")


class TestFormatHealthReport:
    def test_formats_ok_status(self):
        checks = {
            "database": HealthStatus(ok=True, message="Connected"),
            "openai": HealthStatus(ok=True, message="OK"),
        }
        report = format_health_report(checks)
        assert "database" in report
        assert "openai" in report
        assert "All systems operational" in report

    def test_formats_failed_status(self):
        checks = {
            "database": HealthStatus(ok=False, message="Connection failed"),
        }
        report = format_health_report(checks)
        assert "failed" in report
        assert "Some checks failed" in report
