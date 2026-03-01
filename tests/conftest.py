"""
Pytest configuration and fixtures for lex-ai tests.
"""
from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def ensure_project_root(monkeypatch):
    """Ensure tests run with project root in Python path."""
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    monkeypatch.chdir(root)


@pytest.fixture
def mock_openai_key(monkeypatch):
    """Set a dummy OpenAI key for tests that don't call the API."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy-key")
    # Also set in config module if already loaded
    monkeypatch.setattr("src.config.OPENAI_API_KEY", "sk-test-dummy-key", raising=False)
