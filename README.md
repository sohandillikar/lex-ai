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

## Usage

### Scrape documentation

**Option A — CLI:** Run the scraper and enter a URL when prompted:

```bash
python -m src.scrape
```

You’ll be asked for URL, max depth (default 3), and max pages (default 200).

**Option B — MCP:** Use the `scrape_docs` tool from Cursor or Claude Code to crawl and index a URL; no CLI needed.

### Connect to Cursor or Claude Code

After setup, `src.init` will have added the **lex-ai** MCP server to your config. Restart Cursor or Claude Code so they pick it up.

Set `OPENAI_API_KEY` and `DATABASE_URL` in your environment when using Claude Code.

## MCP tools

| Tool           | Description                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| `list_sources` | List indexed documentation sources and chunk counts. Use before searching to get `source_url` values.         |
| `search_docs`  | Semantic search over indexed docs. Args: `query`, optional `source_url`, `limit` (default 5, max 20).         |
| `get_page`     | Return full content of a page by URL (e.g. from a `search_docs` result).                                      |
| `scrape_docs`  | Crawl and index a documentation URL. Args: `url`, optional `max_depth` (default 3), `max_pages` (default 50). |

## Architecture

```
Scrape: URL → Crawl4AI (JS) → Markdown → Chunks (~500 tokens) → OpenAI embeddings → PostgreSQL + pgvector
Query:  Cursor/Claude → MCP → embed query → similarity search → doc chunks
```
