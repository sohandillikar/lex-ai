"""
Tests for src.config.
"""
from __future__ import annotations

import os

import pytest

from src.config import (
    CHUNK_MAX_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    CHUNK_TARGET_TOKENS,
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_PAGES,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    PROJECT_ROOT,
    SERVER_NAME,
)


class TestConfig:
    def test_project_root_exists(self):
        assert PROJECT_ROOT.exists()
        assert (PROJECT_ROOT / "src").exists()

    def test_embedding_model_default(self):
        assert EMBEDDING_MODEL == "text-embedding-3-small"

    def test_embedding_dimensions(self):
        assert EMBEDDING_DIMENSIONS == 1536

    def test_chunk_constants(self):
        assert CHUNK_TARGET_TOKENS > 0
        assert CHUNK_OVERLAP_TOKENS >= 0
        assert CHUNK_MAX_TOKENS >= CHUNK_TARGET_TOKENS

    def test_default_crawl_limits(self):
        assert DEFAULT_MAX_DEPTH >= 1
        assert DEFAULT_MAX_PAGES >= 1

    def test_server_name(self):
        assert SERVER_NAME == "lex-ai"
