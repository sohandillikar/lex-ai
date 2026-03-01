import os
import psycopg
from pgvector.psycopg import register_vector

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/lex_ai",
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
        WITH (m = 16, ef_construction = 64)
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
    cur = conn.execute(
        "DELETE FROM doc_chunks WHERE source_url = %s",
        (source_url,),
    )
    return cur.rowcount


def insert_chunks(conn: psycopg.Connection, chunks: list[dict]) -> int:
    if not chunks:
        return 0
    with conn.cursor() as cur:
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
                for c in chunks
            ],
        )
    return len(chunks)


def search(
    conn: psycopg.Connection,
    query_embedding: list[float],
    source_url: str | None = None,
    limit: int = 5,
    ef_search: int = 40,
) -> list[dict]:
    limit = min(max(limit, 1), 20)

    # Tune HNSW search for this query (higher = better recall, lower = faster)
    conn.execute("SET hnsw.ef_search = %s", (ef_search,))

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


def get_page_chunks(conn: psycopg.Connection, page_url: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, source_url, page_url, title, content
        FROM doc_chunks
        WHERE page_url = %s
        ORDER BY id
        """,
        (page_url,),
    ).fetchall()
    return [
        {
            "id": row[0],
            "source_url": row[1],
            "page_url": row[2],
            "title": row[3],
            "content": row[4],
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
