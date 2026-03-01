"""
Tests for src.db.

These tests mock the database connection. For integration tests with a real
PostgreSQL, run manually.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.db import _row_to_page_chunk, _row_to_search_result, delete_source, insert_chunks, search


class TestRowMappers:
    def test_row_to_search_result(self):
        row = (1, "https://example.com", "https://example.com/page", "Title", "Content here", 0.95)
        result = _row_to_search_result(row)
        assert result["id"] == 1
        assert result["source_url"] == "https://example.com"
        assert result["page_url"] == "https://example.com/page"
        assert result["title"] == "Title"
        assert result["content"] == "Content here"
        assert result["similarity"] == 0.95

    def test_row_to_page_chunk(self):
        row = (1, "https://example.com", "https://example.com/page", "Title", "Content")
        result = _row_to_page_chunk(row)
        assert result["id"] == 1
        assert result["source_url"] == "https://example.com"
        assert result["content"] == "Content"


class TestInsertChunks:
    def test_empty_chunks_returns_zero(self):
        mock_conn = MagicMock()
        assert insert_chunks(mock_conn, []) == 0
        mock_conn.cursor.assert_not_called()

    def test_insert_chunks_calls_executemany(self):
        mock_cur = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_conn.cursor.return_value.__exit__.return_value = False

        chunks = [
            {
                "source_url": "https://example.com",
                "page_url": "https://example.com/p1",
                "title": "Title",
                "content": "Content",
                "embedding": [0.1] * 1536,
            }
        ]
        result = insert_chunks(mock_conn, chunks)
        assert result == 1
        mock_cur.executemany.assert_called_once()


class TestSearch:
    def test_search_returns_empty_list_when_no_results(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = []

        results = search(mock_conn, [0.0] * 1536, limit=5)
        assert results == []
        assert mock_conn.execute.called
