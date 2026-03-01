"""
Central configuration for lex-ai.

Settings can be overridden via environment variables:
- LEX_AI_DATABASE_URL
- LEX_AI_OPENAI_API_KEY
- LEX_AI_EMBEDDING_MODEL
- LEX_AI_EMBEDDING_DIMENSIONS
- LEX_AI_EMBEDDING_BATCH_SIZE
- LEX_AI_CHUNK_TARGET_TOKENS
- LEX_AI_CHUNK_OVERLAP_TOKENS
- LEX_AI_HNSW_EF_SEARCH
"""
from __future__ import annotations

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    os.environ.get("LEX_AI_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lex_ai"),
)

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", os.environ.get("LEX_AI_OPENAI_API_KEY", ""))

# Embeddings
EMBEDDING_MODEL = os.environ.get("LEX_AI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.environ.get("LEX_AI_EMBEDDING_DIMENSIONS", "1536"))
EMBEDDING_BATCH_SIZE = int(os.environ.get("LEX_AI_EMBEDDING_BATCH_SIZE", "200"))
EMBEDDING_MAX_RETRIES = int(os.environ.get("LEX_AI_EMBEDDING_MAX_RETRIES", "3"))

# Chunking
CHUNK_TARGET_TOKENS = int(os.environ.get("LEX_AI_CHUNK_TARGET_TOKENS", "500"))
CHUNK_OVERLAP_TOKENS = int(os.environ.get("LEX_AI_CHUNK_OVERLAP_TOKENS", "50"))
CHUNK_MAX_TOKENS = 8191  # OpenAI text-embedding-3-small per-input limit

# Vector search
HNSW_EF_SEARCH = int(os.environ.get("LEX_AI_HNSW_EF_SEARCH", "40"))
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 64

# Crawl defaults
DEFAULT_MAX_DEPTH = int(os.environ.get("LEX_AI_DEFAULT_MAX_DEPTH", "3"))
DEFAULT_MAX_PAGES = int(os.environ.get("LEX_AI_DEFAULT_MAX_PAGES", "200"))

# MCP
SERVER_NAME = "lex-ai"
