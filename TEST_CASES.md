# MCP Test Cases

Use these prompts in Cursor (with the Lex AI MCP enabled) to verify the Documentation MCP. Use a niche API so Cursor relies on your indexed docs rather than training data. Example: index **Unkey** (https://unkey.com/docs) first via `scrape_docs`, then run these.

---

## 1. List sources

**Prompt:** What documentation sources are currently indexed in my Lex AI MCP? List each source and how many chunks it has.

*Expected:* MCP calls `list_sources` and returns the list, or a message that no docs are indexed yet.

---

## 2. Search docs (niche: Unkey)

**Prompt:** Search my indexed documentation for how to **create and verify API keys** with Unkey. Return the top 3 relevant results with their URLs and similarity scores.

*Expected:* MCP calls `search_docs` with a query like "create and verify API keys Unkey" and returns formatted results from the Unkey docs.

---

## 3. Get full page

**Prompt:** Get the full content of the Unkey documentation page you found about verification (use the exact `page_url` from your previous search result).

*Expected:* MCP calls `get_page` with that URL and returns the full page body.

---

## 4. Scrape new docs (niche: Unkey)

**Prompt:** Use the Lex AI MCP to scrape and index the Unkey docs from `https://unkey.com/docs` with max depth 2 and at most 20 pages. After it finishes, list the indexed sources again.

*Expected:* `scrape_docs` returns immediately (runs in background). Wait 5–10 minutes, then run `list_sources` to confirm the Unkey source appears. Use `search_docs` to query.
