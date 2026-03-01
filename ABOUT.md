# About Lex AI MCP

## What is Lex?

**Lex AI** is an MCP server that lets LLMs in **Cursor** or **Claude Code** use your own documentation as context. It **scrapes** documentation from any URL (using Playwright & Crawl4AI), **chunks** it, **embeds** with OpenAI, and **stores** in PostgreSQL with pgvector. The LLM can then **search** that knowledge base and **fetch** documents via MCP tools, so that answers are grounded in your chosen docs (internal, niche, or third-party) instead of only model training data.

## Pain points and how Lex addresses them

Lex addresses the following pain points:

### 1. Models don't know your docs

Niche, private, or internal documentation isn't in training data, so the assistant hallucinates and writes broken code. Lex AI lets you **scrape and index** any doc site via `scrape_docs` tool. Once indexed, **semantic search** (`search_docs`) and **full-page retrieval** (`get_page`) give the assistant accurate context from your sources.

### 2. Constant context switching

Developers repeatedly leave the editor to open browsers and search docs. MCP tools run **inside** Cursor/Claude Code: the assistant calls `search_docs` and `get_page` during the conversation, so you stay in the IDE and get answers grounded in your indexed docs.

### 3. Re-scraping every time is slow

Fetching and parsing documentation on every query would be slow and redundant. Lex AI **saves** all scraped content in PostgreSQL. You run `scrape_docs` once (or when you want to refresh a source); after that, `search_docs` and `get_page` read from the database, so the assistant gets answers quickly without re-crawling.

### 4. JS-heavy doc sites

Many docs are SPAs; simple HTTP fetch misses content. The scraper uses **Crawl4AI with Playwright** so pages are rendered like a browser before being converted to markdown and chunked, so JS-rendered docs are fully indexed.

### 5. Finding the right passage

Full pages are too long for context and keyword search often misses the right snippet. Content is **chunked**, **embedded** with OpenAI, and stored in **pgvector**. The assistant uses **similarity search** so results are relevant passages, not just keyword matches.

---

For setup and tool details, see [README.md](README.md).
