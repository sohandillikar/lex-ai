import os
import psycopg
from pgvector.psycopg import register_vector

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/docs_mcp",
)


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def init_db(conn: psycopg.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doc_chunks (
            id BIGSERIAL PRIMARY KEY,
            source_url TEXT NOT NULL,
            page_url TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            embedding vector(1536),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding
        ON doc_chunks USING hnsw (embedding vector_cosine_ops)
    """)


def delete_source(conn: psycopg.Connection, source_url: str) -> int:
    cur = conn.execute(
        "DELETE FROM doc_chunks WHERE source_url = %s",
        (source_url,),
    )
    return cur.rowcount


def insert_chunks(conn: psycopg.Connection, chunks: list[dict]) -> int:
    if not chunks:
        return 0
    with conn.cursor() as cur:
        for chunk in chunks:
            cur.execute(
                """
                INSERT INTO doc_chunks (source_url, page_url, title, content, embedding)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    chunk["source_url"],
                    chunk["page_url"],
                    chunk.get("title"),
                    chunk["content"],
                    chunk["embedding"],
                ),
            )
    return len(chunks)


def search(
    conn: psycopg.Connection,
    query_embedding: list[float],
    source_url: str | None = None,
    limit: int = 5,
) -> list[dict]:
    limit = min(max(limit, 1), 20)

    if source_url:
        rows = conn.execute(
            """
            SELECT id, source_url, page_url, title, content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM doc_chunks
            WHERE source_url = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, source_url, query_embedding, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, source_url, page_url, title, content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM doc_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, limit),
        ).fetchall()

    return [
        {
            "id": row[0],
            "source_url": row[1],
            "page_url": row[2],
            "title": row[3],
            "content": row[4],
            "similarity": float(row[5]),
        }
        for row in rows
    ]


def list_sources(conn: psycopg.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT source_url FROM doc_chunks ORDER BY source_url"
    ).fetchall()
    return [row[0] for row in rows]


def list_sources_with_counts(conn: psycopg.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT source_url, COUNT(*) AS chunk_count FROM doc_chunks GROUP BY source_url ORDER BY source_url"
    ).fetchall()
    return [{"source_url": row[0], "chunk_count": row[1]} for row in rows]
