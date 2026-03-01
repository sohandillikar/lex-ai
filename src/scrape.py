"""
Scraper and indexer for lex-ai.

Crawls documentation sites, chunks content, generates embeddings, and stores in the database.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from src.chunker import chunk_markdown
from src.config import DEFAULT_MAX_DEPTH, DEFAULT_MAX_PAGES
from src.db import delete_source, get_connection, init_db, insert_chunks
from src.embeddings import embed_texts
from src.exceptions import CrawlError, ValidationError
from src.types import Chunk
from src.url_utils import ensure_scheme, normalize_source_url, validate_url

logger = logging.getLogger(__name__)


async def crawl_and_index(
    url: str,
    max_depth: int,
    max_pages: int,
    conn=None,
    *,
    dry_run: bool = False,
    verbose: bool = True,
) -> str:
    """
    Crawl a documentation URL and index it for semantic search.

    Args:
        url: Documentation base URL to crawl.
        max_depth: Maximum link depth to follow.
        max_pages: Maximum number of pages to crawl.
        conn: Optional database connection. If None, one is created.
        dry_run: If True, crawl and chunk but do not embed or store.
        verbose: If True, show progress and status messages.

    Returns:
        Summary string of the operation.
    """
    url = ensure_scheme(url.strip())
    valid, err = validate_url(url)
    if not valid:
        raise ValidationError(err or "Invalid URL", hint="Use a URL like https://docs.example.com")

    source_url = normalize_source_url(url)
    owns_conn = conn is None

    def log(msg: str) -> None:
        if verbose:
            logger.info(msg)
            print(msg, flush=True)

    if owns_conn:
        log("\n--- Connecting to database ---")
        conn = get_connection()
        init_db(conn)

    if not dry_run:
        existing = delete_source(conn, source_url)
        if existing:
            log(f"Removed {existing} existing chunks for {source_url}")

    log(f"\n--- Crawling {url} (depth={max_depth}, max_pages={max_pages}) ---\n")

    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=max_depth,
            include_external=False,
            max_pages=max_pages,
        ),
        markdown_generator=DefaultMarkdownGenerator(),
        verbose=False,
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url, config=config)

    if not isinstance(results, list):
        results = [results]

    successful = [r for r in results if r.success and r.markdown and r.markdown.strip()]
    log(f"Crawled {len(results)} pages, {len(successful)} with content\n")

    if not successful:
        if owns_conn:
            conn.close()
        raise CrawlError(
            f"No content found from {source_url}",
            hint="Check the URL and ensure the site is accessible.",
        )

    log("--- Chunking pages ---")
    all_chunks: list[Chunk] = []
    for result in tqdm(successful, desc="Chunking", unit="page", disable=not verbose):
        page_chunks = chunk_markdown(
            markdown=result.markdown,
            page_url=result.url,
            source_url=source_url,
        )
        all_chunks.extend(page_chunks)
    log(f"Created {len(all_chunks)} chunks from {len(successful)} pages\n")

    if not all_chunks:
        if owns_conn:
            conn.close()
        raise CrawlError(
            f"No chunks created from {source_url}",
            hint="The pages may have had no meaningful content.",
        )

    if dry_run:
        if owns_conn:
            conn.close()
        return f"Dry run: would index {len(all_chunks)} chunks from {len(successful)} pages at {source_url}"

    log("--- Generating embeddings ---")
    texts = [c["content"] for c in all_chunks]

    def make_progress_callback(pbar: tqdm):
        prev = [0]
        def cb(completed: int, _total: int) -> None:
            pbar.update(completed - prev[0])
            prev[0] = completed
        return cb

    with tqdm(total=len(texts), desc="Embeddings", unit="chunk", disable=not verbose) as pbar:
        embeddings = embed_texts(texts, on_progress=make_progress_callback(pbar))
    for chunk, embedding in zip(all_chunks, embeddings, strict=False):
        chunk["embedding"] = embedding
    log(f"Generated {len(embeddings)} embeddings\n")

    log("--- Storing in database ---")
    count = insert_chunks(conn, all_chunks)
    log(f"Stored {count} chunks\n")

    if owns_conn:
        conn.close()

    summary = f"Done! Scraped {len(successful)} pages, created {count} chunks from {source_url}."
    log(summary)
    return summary


def main() -> None:
    """CLI entry point for the scraper."""
    parser = argparse.ArgumentParser(
        description="Scrape and index documentation for semantic search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.scrape https://docs.example.com
  python -m src.scrape --max-pages 100 --max-depth 2 https://docs.stripe.com
  python -m src.scrape --dry-run https://docs.example.com
        """,
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Documentation URL to scrape (e.g. https://docs.example.com)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=DEFAULT_MAX_DEPTH,
        metavar="N",
        help=f"Max crawl depth (default: {DEFAULT_MAX_DEPTH})",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        metavar="N",
        help=f"Max pages to crawl (default: {DEFAULT_MAX_PAGES})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Crawl and chunk but do not embed or store",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Reduce output (no progress bars)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    url = args.url
    if not url:
        print("Documentation Scraper & Indexer", flush=True)
        print("=" * 60, flush=True)
        url = input("\nPaste the documentation URL: ").strip()
        if not url:
            print("No URL provided. Exiting.", flush=True)
            sys.exit(1)
        try:
            max_depth = input(f"Max crawl depth [{args.max_depth}]: ").strip() or str(args.max_depth)
            args.max_depth = int(max_depth)
        except ValueError:
            pass
        try:
            max_pages = input(f"Max pages to crawl [{args.max_pages}]: ").strip() or str(args.max_pages)
            args.max_pages = int(max_pages)
        except ValueError:
            pass

    verbose = not args.quiet

    try:
        result = asyncio.run(
            crawl_and_index(
                url,
                args.max_depth,
                args.max_pages,
                dry_run=args.dry_run,
                verbose=verbose,
            )
        )
        print(result, flush=True)
    except (ValidationError, CrawlError, Exception) as e:
        logger.exception("Scrape failed")
        print(f"Error: {e}", file=sys.stderr, flush=True)
        if hasattr(e, "hint") and e.hint:
            print(f"Hint: {e.hint}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
