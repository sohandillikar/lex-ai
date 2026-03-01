"""
Type definitions for lex-ai.

Uses TypedDict for structural typing of chunk and search result payloads.
"""
from __future__ import annotations

from typing import TypedDict


class Chunk(TypedDict, total=False):
    """A document chunk ready for embedding and storage."""

    source_url: str
    page_url: str
    title: str | None
    content: str
    embedding: list[float]


class SearchResult(TypedDict):
    """A single semantic search result."""

    id: int
    source_url: str
    page_url: str
    title: str | None
    content: str
    similarity: float


class SourceInfo(TypedDict):
    """Metadata about an indexed documentation source."""

    source_url: str
    chunk_count: int


class PageChunk(TypedDict):
    """A chunk as returned by get_page_chunks (no similarity)."""

    id: int
    source_url: str
    page_url: str
    title: str | None
    content: str
