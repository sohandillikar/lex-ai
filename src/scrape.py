import asyncio
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from src.chunker import chunk_markdown
from src.embeddings import embed_texts
from src.db import get_connection, init_db, delete_source, insert_chunks

DEFAULT_MAX_DEPTH = 3
DEFAULT_MAX_PAGES = 200


def _normalize_source_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


async def crawl_and_index(url: str, max_depth: int, max_pages: int) -> None:
    source_url = _normalize_source_url(url)

    print(f"\n--- Connecting to database ---")
    conn = get_connection()
    init_db(conn)

    existing = delete_source(conn, source_url)
    if existing:
        print(f"Removed {existing} existing chunks for {source_url}")

    print(f"\n--- Crawling {url} (depth={max_depth}, max_pages={max_pages}) ---\n")

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
    print(f"Crawled {len(results)} pages, {len(successful)} with content\n")

    if not successful:
        print("No content found. Check the URL and try again.")
        conn.close()
        return

    print("--- Chunking pages ---")
    all_chunks: list[dict] = []
    for result in successful:
        page_chunks = chunk_markdown(
            markdown=result.markdown,
            page_url=result.url,
            source_url=source_url,
        )
        all_chunks.extend(page_chunks)
    print(f"Created {len(all_chunks)} chunks from {len(successful)} pages\n")

    if not all_chunks:
        print("No chunks created. The pages may have had no meaningful content.")
        conn.close()
        return

    print("--- Generating embeddings ---")
    texts = [c["content"] for c in all_chunks]
    embeddings = embed_texts(texts)
    for chunk, embedding in zip(all_chunks, embeddings):
        chunk["embedding"] = embedding
    print(f"Generated {len(embeddings)} embeddings\n")

    print("--- Storing in database ---")
    count = insert_chunks(conn, all_chunks)
    print(f"Stored {count} chunks\n")

    conn.close()
    print(f"Done! Documentation from {source_url} is now indexed and searchable.")


def main() -> None:
    print("=" * 60)
    print("  Documentation Scraper & Indexer")
    print("=" * 60)

    url = input("\nPaste the documentation URL: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        sys.exit(1)

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        max_depth = int(input(f"Max crawl depth [{DEFAULT_MAX_DEPTH}]: ").strip() or DEFAULT_MAX_DEPTH)
    except ValueError:
        max_depth = DEFAULT_MAX_DEPTH

    try:
        max_pages = int(input(f"Max pages to crawl [{DEFAULT_MAX_PAGES}]: ").strip() or DEFAULT_MAX_PAGES)
    except ValueError:
        max_pages = DEFAULT_MAX_PAGES

    asyncio.run(crawl_and_index(url, max_depth, max_pages))


if __name__ == "__main__":
    main()
