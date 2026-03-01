from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP
from src.embeddings import embed_query
from src.db import get_connection, init_db, search, list_sources_with_counts

mcp = FastMCP("Documentation Search")

_conn = None


def _get_conn():
    global _conn
    if _conn is None:
        _conn = get_connection()
        init_db(_conn)
    return _conn


@mcp.tool()
def list_sources() -> str:
    """List all documentation sources that have been indexed and are available for search.

    Call this tool first to discover what documentation is available before
    searching, so you can use the correct source_url filter in search_docs.
    """
    conn = _get_conn()
    sources = list_sources_with_counts(conn)
    if not sources:
        return "No documentation has been indexed yet. Run scrape.py first to index some docs."
    lines = [f"- {s['source_url']} ({s['chunk_count']} chunks)" for s in sources]
    return "Indexed documentation sources:\n" + "\n".join(lines)


@mcp.tool()
def search_docs(query: str, source_url: str = "", limit: int = 5) -> str:
    """Search the documentation knowledge base.

    Use this tool to find relevant documentation, code examples, and API
    references from previously indexed documentation sites. Call list_sources
    first to discover available sources and get the correct source_url values.

    Args:
        query: The search query describing what you're looking for.
               Be specific for better results, e.g. "How to create a payment
               intent with Stripe" rather than just "payments".
        source_url: Optional filter to search within a specific documentation
                    source. Use a value from list_sources (e.g.
                    "https://docs.stripe.com"). Leave empty to search across
                    all indexed docs.
        limit: Number of results to return (default 5, max 20).
    """
    conn = _get_conn()

    if not query.strip():
        return "Please provide a search query. Use the list_sources tool to discover available documentation."

    query_embedding = embed_query(query)
    results = search(
        conn,
        query_embedding,
        source_url=source_url if source_url.strip() else None,
        limit=limit,
    )

    if not results:
        return f"No results found for: {query}"

    parts: list[str] = []
    for i, r in enumerate(results, 1):
        header = f"## Result {i}"
        if r["title"]:
            header += f" — {r['title']}"
        header += f" (similarity: {r['similarity']:.3f})"
        parts.append(header)
        parts.append(f"**Source:** {r['page_url']}")
        parts.append("")
        parts.append(r["content"])
        parts.append("")

    return "\n".join(parts)


if __name__ == "__main__":
    mcp.run()
