"""
Tests for src.chunker.
"""
from __future__ import annotations

import pytest

from src.chunker import chunk_markdown


class TestChunkMarkdown:
    def test_empty_string_returns_empty_list(self):
        assert chunk_markdown("", "https://example.com", "https://example.com") == []

    def test_whitespace_only_returns_empty_list(self):
        assert chunk_markdown("   \n\n  ", "https://example.com", "https://example.com") == []

    def test_simple_paragraph(self):
        md = "This is a simple paragraph of text."
        chunks = chunk_markdown(md, "https://example.com/page", "https://example.com")
        assert len(chunks) == 1
        assert chunks[0]["content"] == "This is a simple paragraph of text."
        assert chunks[0]["page_url"] == "https://example.com/page"
        assert chunks[0]["source_url"] == "https://example.com"
        assert chunks[0]["title"] is None

    def test_header_sections(self):
        md = """# Introduction

Welcome to the docs.

## Getting Started

First step here.

## Next Steps

More content.
"""
        chunks = chunk_markdown(md, "https://docs.example.com/start", "https://docs.example.com")
        assert len(chunks) >= 2
        titles = [c["title"] for c in chunks if c.get("title")]
        assert "Introduction" in titles or any("Introduction" in (c.get("title") or "") for c in chunks)
        assert "Getting Started" in titles or any("Getting Started" in (c.get("title") or "") for c in chunks)

    def test_long_text_splits_into_chunks(self):
        md = " ".join(["word"] * 500)  # Long paragraph
        chunks = chunk_markdown(md, "https://example.com", "https://example.com")
        assert len(chunks) >= 2
        total_content = " ".join(c["content"] for c in chunks)
        assert "word" in total_content

    def test_preserves_source_and_page_urls(self):
        md = "Short text."
        chunks = chunk_markdown(md, "https://example.com/specific/page", "https://example.com")
        assert chunks[0]["page_url"] == "https://example.com/specific/page"
        assert chunks[0]["source_url"] == "https://example.com"
