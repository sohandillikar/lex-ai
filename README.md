# Lex AI

Scrape documentation from any URL and search it via an MCP server in Cursor or Claude Code. Content is crawled (with JS rendering), chunked, embedded with OpenAI, and stored in PostgreSQL with pgvector.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key

## Setup

**macOS / Linux (or Git Bash / WSL on Windows):**
```bash
./setup.sh
```

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

**Any platform (run directly with Python):**
```bash
python setup.py
```

This starts PostgreSQL, installs Python dependencies and Playwright browsers (Crawl4AI), creates `.env` from `.env.example` if needed, and runs the MCP config wizard. Edit `.env` to add your OpenAI API key if you just created it.

**Non-interactive setup:** Set `LEX_AI_MCP_CLIENT=cursor` or `LEX_AI_MCP_CLIENT=claude` to skip the client prompt.

## Usage

### Scrape documentation

**Option A — CLI:** Run the scraper with arguments or interactively:

```bash
python -m src.scrape https://docs.example.com --max-pages 100
python -m src.scrape --dry-run https://docs.example.com
python -m src.scrape  # prompts for URL
```

**Option B — MCP:** Use the `scrape_docs` tool from Cursor or Claude Code to crawl and index a URL; no CLI needed.

### Configure MCP client

```bash
python -m src.init --cursor   # For Cursor (~/.cursor/mcp.json)
python -m src.init --claude   # For Claude Code (.mcp.json)
```

After setup, restart Cursor or Claude Code. Set `OPENAI_API_KEY` and `DATABASE_URL` when using Claude Code.

## Configuration

Override defaults via environment variables: `LEX_AI_EMBEDDING_BATCH_SIZE`, `LEX_AI_CHUNK_TARGET_TOKENS`, `LEX_AI_DEFAULT_MAX_DEPTH`, `LEX_AI_DEFAULT_MAX_PAGES`, etc. See `src/config.py` for all options.

## MCP tools

| Tool           | Description                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| `list_sources` | List indexed documentation sources and chunk counts. Use before searching to get `source_url` values.         |
| `search_docs`  | Semantic search over indexed docs. Args: `query`, optional `source_url`, `limit` (default 5, max 20).         |
| `get_page`     | Return full content of a page by URL (e.g. from a `search_docs` result).                                      |
| `scrape_docs`  | Crawl and index a documentation URL. Args: `url`, optional `max_depth` (default 3), `max_pages` (default 50). |
| `health_check` | Verify PostgreSQL and OpenAI connectivity. Use before scraping to confirm setup.                             |

## Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Architecture

```
Scrape: URL → Crawl4AI (JS) → Markdown → Chunks (~500 tokens) → OpenAI embeddings → PostgreSQL + pgvector
Query:  Cursor/Claude → MCP → embed query → similarity search → doc chunks
```
