"""
Tests for src.url_utils.
"""
from __future__ import annotations

import pytest

from src.url_utils import ensure_scheme, is_valid_url, normalize_source_url, validate_url


class TestNormalizeSourceUrl:
    def test_extracts_scheme_and_netloc(self):
        assert normalize_source_url("https://docs.example.com/path/to/page") == "https://docs.example.com"
        assert normalize_source_url("http://localhost:3000/foo") == "http://localhost:3000"

    def test_handles_root_url(self):
        assert normalize_source_url("https://docs.example.com") == "https://docs.example.com"
        assert normalize_source_url("https://docs.example.com/") == "https://docs.example.com"


class TestEnsureScheme:
    def test_adds_https_when_missing(self):
        assert ensure_scheme("docs.example.com") == "https://docs.example.com"
        assert ensure_scheme("example.com/path") == "https://example.com/path"

    def test_preserves_existing_scheme(self):
        assert ensure_scheme("https://example.com") == "https://example.com"
        assert ensure_scheme("http://example.com") == "http://example.com"

    def test_respects_default_param(self):
        assert ensure_scheme("example.com", default="http") == "http://example.com"


class TestValidateUrl:
    def test_valid_urls(self):
        valid, err = validate_url("https://docs.example.com")
        assert valid is True
        assert err is None

        valid, err = validate_url("http://localhost:8080")
        assert valid is True

        valid, err = validate_url("docs.stripe.com")
        assert valid is True  # ensure_scheme adds https

    def test_empty_url(self):
        valid, err = validate_url("")
        assert valid is False
        assert "empty" in err.lower()

    def test_invalid_scheme(self):
        valid, err = validate_url("ftp://example.com")
        assert valid is False
        assert "scheme" in err.lower()


class TestIsValidUrl:
    def test_returns_bool(self):
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("") is False
