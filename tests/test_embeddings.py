"""
Tests for src.embeddings.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.embeddings import embed_query, embed_texts


class TestEmbedTexts:
    def test_empty_list_returns_empty(self):
        assert embed_texts([]) == []

    @pytest.mark.skip(reason="Requires OpenAI API; run manually with valid key")
    def test_embed_texts_integration(self):
        result = embed_texts(["hello world"])
        assert len(result) == 1
        assert len(result[0]) == 1536

    def test_on_progress_callback_called(self):
        with patch("src.embeddings._get_client") as mock_get:
            mock_resp = MagicMock()
            mock_resp.data = [MagicMock(embedding=[0.1] * 1536)]
            mock_client = MagicMock()
            mock_client.embeddings.create.return_value = mock_resp
            mock_get.return_value = mock_client

            progress_log = []

            def cb(completed: int, total: int):
                progress_log.append((completed, total))

            result = embed_texts(["test"], on_progress=cb)
            assert len(result) == 1
            assert len(progress_log) >= 1
            assert progress_log[-1] == (1, 1)


class TestEmbedQuery:
    def test_returns_single_embedding(self):
        with patch("src.embeddings.embed_texts") as mock_embed:
            mock_embed.return_value = [[0.1] * 1536]
            result = embed_query("test query")
            assert len(result) == 1536
            mock_embed.assert_called_once_with(["test query"], on_progress=None)
