"""
MCP server for lex-ai.

Exposes documentation search and scrape tools to Cursor and Claude Code.
All heavy imports are lazy to keep startup fast.
"""
from __future__ import annotations

import sys

# Line-buffer stdout so MCP JSON-RPC responses flush immediately
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Documentation Search")

_conn = None


def _get_conn():
    global _conn
    if _conn is None:
        from dotenv import load_dotenv
        load_dotenv()
        from src.db import get_connection, init_db
        _conn = get_connection()
        init_db(_conn)
    return _conn


@mcp.tool()
def list_sources() -> str:
    """List all documentation sources that have been indexed and are available for search.

    Call this tool first to discover what documentation is available before
    searching, so you can use the correct source_url filter in search_docs.
    """
    from src.db import list_sources_with_counts
    conn = _get_conn()
    sources = list_sources_with_counts(conn)
    if not sources:
        return "No documentation has been indexed yet. Run scrape_docs or python -m src.scrape to index some docs."
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
    from src.db import search
    from src.embeddings import embed_query
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


@mcp.tool()
def get_page(page_url: str) -> str:
    """Retrieve the full content of a specific documentation page by its URL.

    Use this after search_docs returns a relevant result and you need more
    context from the same page. Pass the page_url value from the search result.

    Args:
        page_url: The exact page URL as returned by search_docs.
    """
    from src.db import get_page_chunks
    conn = _get_conn()
    chunks = get_page_chunks(conn, page_url)

    if not chunks:
        return f"No content found for page: {page_url}"

    title = chunks[0]["title"] or "Untitled"
    source = chunks[0]["source_url"]
    body = "\n\n".join(c["content"] for c in chunks)

    return f"# {title}\n**Source:** {page_url} (from {source})\n\n{body}"


@mcp.tool()
def health_check() -> str:
    """Check that the lex-ai MCP server can connect to PostgreSQL and the OpenAI API.

    Use this to verify your setup before scraping or searching. Returns status
    for each dependency.
    """
    from src.health import check_all, format_health_report
    checks = check_all()
    return format_health_report(checks)


@mcp.tool()
def scrape_docs(url: str, max_depth: int = 3, max_pages: int = 50, background: bool = True) -> str:
    """Scrape and index documentation from a URL so it becomes searchable.

    This crawls the documentation site, converts pages to markdown, chunks
    the content, generates embeddings, and stores everything in the database.
    After scraping, the documentation will be available via search_docs.

    By default runs in background so the chat doesn't timeout. Use list_sources
    after a few minutes to check when indexing is complete.

    Args:
        url: The documentation URL to scrape (e.g. "https://unkey.com/docs").
        max_depth: How many link levels deep to crawl (default 3).
        max_pages: Maximum number of pages to crawl (default 50).
        background: If True (default), run in background and return immediately.
                    If False, wait for completion (may timeout on large scrapes).
    """
    if not url.strip():
        return "Please provide a URL to scrape."

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    import subprocess
    from src.config import PROJECT_ROOT

    if background:
        # Run in subprocess so MCP returns immediately; scrape continues independently
        subprocess.Popen(
            [sys.executable, "-m", "src.scrape", url, "--max-depth", str(max_depth), "--max-pages", str(max_pages)],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return f"Scraping started in background: {url} (depth={max_depth}, max_pages={max_pages}). This typically takes 5–10 minutes. Run list_sources in a few minutes to check when it's done, then search_docs to query the indexed docs."
    else:
        # Synchronous: may timeout on large scrapes
        import asyncio
        from src.scrape import crawl_and_index
        conn = _get_conn()
        return asyncio.run(crawl_and_index(url, max_depth, max_pages, conn=conn, verbose=True))


if __name__ == "__main__":
    mcp.run()
