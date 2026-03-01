# Documentation MCP Server

Scrape API/SDK documentation from any URL and query it through an MCP server in Cursor or Claude Code.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key

## Setup

### 1. Start PostgreSQL with pgvector

```bash
docker compose up -d
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
crawl4ai-setup  # installs Playwright browsers for JS rendering
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### Scrape documentation

Run the scraper and paste a documentation URL when prompted:

```bash
python -m src.scrape
```

You'll be asked for:

- **URL** — the documentation site to scrape (e.g. `https://docs.stripe.com/`)
- **Max depth** — how many link levels deep to crawl (default: 3)
- **Max pages** — safety limit on total pages (default: 200)

The scraper will crawl the site, chunk the content, generate embeddings, and store everything in PostgreSQL.

### Connect to Cursor

Add the MCP server to your Cursor configuration at `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "lex-ai": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/documentation-mcp2",
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/lex_ai",
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

### Connect to Claude Code

```bash
claude mcp add lex-ai -- python -m src.server
```

Set the required environment variables (`DATABASE_URL`, `OPENAI_API_KEY`) in your shell before running Claude Code.

## MCP Tool

The server exposes a single tool:

### `search_docs`

| Parameter    | Type   | Default | Description                                                      |
| ------------ | ------ | ------- | ---------------------------------------------------------------- |
| `query`      | string | —       | What you're looking for in the docs                              |
| `source_url` | string | `""`    | Filter to a specific doc source (e.g. `https://docs.stripe.com`) |
| `limit`      | int    | `5`     | Number of results (max 20)                                       |

## Architecture

```
User pastes URL
  → Crawl4AI (deep crawl with JS rendering)
  → Markdown conversion
  → Text chunking (~500 tokens)
  → OpenAI embeddings (text-embedding-3-small)
  → PostgreSQL + pgvector

Cursor/Claude Code
  → MCP stdio server
  → Embed query → cosine similarity search
  → Return relevant documentation chunks
```
