"""
Embedding layer for lex-ai.

Generates vector embeddings via OpenAI API with batching and retries.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from openai import OpenAI

from src.config import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MAX_RETRIES,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
)
from src.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
            raise EmbeddingError(
                "OPENAI_API_KEY is not set",
                hint="Add it to your .env file or set the environment variable.",
            )
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embed_texts(
    texts: list[str],
    *,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[list[float]]:
    """Generate embeddings for a list of texts. Batches requests for efficiency."""
    if not texts:
        return []

    client = _get_client()
    all_embeddings: list[list[float]] = []
    total = len(texts)

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]
        for attempt in range(1, EMBEDDING_MAX_RETRIES + 1):
            try:
                response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                if on_progress:
                    on_progress(len(all_embeddings), total)
                break
            except Exception as e:
                if attempt == EMBEDDING_MAX_RETRIES:
                    raise EmbeddingError(
                        f"Embedding API failed after {EMBEDDING_MAX_RETRIES} attempts: {e}",
                        hint="Check your API key and network connectivity.",
                    ) from e
                delay = 2**attempt
                logger.warning("Embedding batch failed (attempt %d/%d), retrying in %ds: %s", attempt, EMBEDDING_MAX_RETRIES, delay, e)
                time.sleep(delay)

    return all_embeddings


def embed_query(text: str) -> list[float]:
    """Generate embedding for a single query string."""
    return embed_texts([text])[0]
