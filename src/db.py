"""
Database layer for lex-ai.

Handles PostgreSQL + pgvector connections, schema, and vector search.
"""
from __future__ import annotations

import logging
from typing import Any

import psycopg
from pgvector.psycopg import register_vector

from src.config import (
    DATABASE_URL,
    EMBEDDING_DIMENSIONS,
    HNSW_EF_CONSTRUCTION,
    HNSW_EF_SEARCH,
    HNSW_M,
)
from src.types import Chunk, PageChunk, SearchResult, SourceInfo

logger = logging.getLogger(__name__)


def get_connection() -> psycopg.Connection:
    """Create a new database connection with pgvector registered."""
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def init_db(conn: psycopg.Connection) -> None:
    """Create tables and indexes if they do not exist."""
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS doc_chunks (
            id BIGSERIAL PRIMARY KEY,
            source_url TEXT NOT NULL,
            page_url TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            embedding vector({EMBEDDING_DIMENSIONS}),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding
        ON doc_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION})
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_doc_chunks_source_url
        ON doc_chunks (source_url)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_doc_chunks_page_url
        ON doc_chunks (page_url)
    """)


def delete_source(conn: psycopg.Connection, source_url: str) -> int:
    """Remove all chunks for a given source. Returns count deleted."""
    cur = conn.execute(
        "DELETE FROM doc_chunks WHERE source_url = %s",
        (source_url,),
    )
    return cur.rowcount


def insert_chunks(conn: psycopg.Connection, chunks: list[Chunk]) -> int:
    """Insert chunks into the database. Uses batched executemany for efficiency."""
    if not chunks:
        return 0

    batch_size = 500
    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            cur.executemany(
                """
                INSERT INTO doc_chunks (source_url, page_url, title, content, embedding)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [
                    (
                        c["source_url"],
                        c["page_url"],
                        c.get("title"),
                        c["content"],
                        c["embedding"],
                    )
                    for c in batch
                ],
            )
            total += len(batch)
    return total


def _row_to_search_result(row: tuple[Any, ...]) -> SearchResult:
    """Map a database row to a SearchResult dict."""
    return {
        "id": row[0],
        "source_url": row[1],
        "page_url": row[2],
        "title": row[3],
        "content": row[4],
        "similarity": float(row[5]),
    }


def _row_to_page_chunk(row: tuple[Any, ...]) -> PageChunk:
    """Map a database row to a PageChunk dict."""
    return {
        "id": row[0],
        "source_url": row[1],
        "page_url": row[2],
        "title": row[3],
        "content": row[4],
    }


def search(
    conn: psycopg.Connection,
    query_embedding: list[float],
    source_url: str | None = None,
    limit: int = 5,
    ef_search: int | None = None,
) -> list[SearchResult]:
    """Semantic search over doc_chunks using cosine similarity."""
    limit = min(max(limit, 1), 20)
    ef = ef_search if ef_search is not None else HNSW_EF_SEARCH

    conn.execute("SET hnsw.ef_search = %s", (ef,))

    if source_url:
        rows = conn.execute(
            """
            WITH q AS (SELECT %s::vector AS v)
            SELECT id, source_url, page_url, title, content,
                   1 - (embedding <=> (SELECT v FROM q)) AS similarity
            FROM doc_chunks
            WHERE source_url = %s
            ORDER BY embedding <=> (SELECT v FROM q)
            LIMIT %s
            """,
            (query_embedding, source_url, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            WITH q AS (SELECT %s::vector AS v)
            SELECT id, source_url, page_url, title, content,
                   1 - (embedding <=> (SELECT v FROM q)) AS similarity
            FROM doc_chunks
            ORDER BY embedding <=> (SELECT v FROM q)
            LIMIT %s
            """,
            (query_embedding, limit),
        ).fetchall()

    return [_row_to_search_result(row) for row in rows]


def get_page_chunks(conn: psycopg.Connection, page_url: str) -> list[PageChunk]:
    """Retrieve all chunks for a given page URL."""
    rows = conn.execute(
        """
        SELECT id, source_url, page_url, title, content
        FROM doc_chunks
        WHERE page_url = %s
        ORDER BY id
        """,
        (page_url,),
    ).fetchall()
    return [_row_to_page_chunk(row) for row in rows]


def list_sources(conn: psycopg.Connection) -> list[str]:
    """List distinct source URLs."""
    rows = conn.execute(
        "SELECT DISTINCT source_url FROM doc_chunks ORDER BY source_url"
    ).fetchall()
    return [row[0] for row in rows]


def list_sources_with_counts(conn: psycopg.Connection) -> list[SourceInfo]:
    """List sources with chunk counts."""
    rows = conn.execute(
        "SELECT source_url, COUNT(*) AS chunk_count FROM doc_chunks GROUP BY source_url ORDER BY source_url"
    ).fetchall()
    return [{"source_url": row[0], "chunk_count": row[1]} for row in rows]
