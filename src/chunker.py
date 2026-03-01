"""
Chunking logic for lex-ai.

Splits markdown into semantic chunks suitable for embedding.
"""
from __future__ import annotations

import re

import tiktoken

from src.config import (
    CHUNK_MAX_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    CHUNK_TARGET_TOKENS,
)
from src.types import Chunk

_encoder = tiktoken.get_encoding("cl100k_base")

_HEADER_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
_SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")


def _token_len(text: str) -> int:
    return len(_encoder.encode(text))


def _split_by_headers(markdown: str) -> list[dict]:
    """Split markdown into sections based on h1/h2/h3 headers."""
    sections: list[dict] = []
    last_end = 0
    current_title: str | None = None

    for match in _HEADER_PATTERN.finditer(markdown):
        if match.start() > last_end:
            text = markdown[last_end : match.start()].strip()
            if text:
                sections.append({"title": current_title, "text": text})
        current_title = match.group(2).strip()
        last_end = match.end()

    trailing = markdown[last_end:].strip()
    if trailing:
        sections.append({"title": current_title, "text": trailing})

    if not sections and markdown.strip():
        sections.append({"title": None, "text": markdown.strip()})

    return sections


def _split_to_target(text: str, target: int) -> list[str]:
    """Recursively split text to fit within the token target."""
    if _token_len(text) <= target:
        return [text] if text.strip() else []

    paragraphs = re.split(r"\n\n+", text)
    if len(paragraphs) > 1:
        chunks: list[str] = []
        current = ""
        for para in paragraphs:
            candidate = f"{current}\n\n{para}".strip() if current else para
            if _token_len(candidate) <= target:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if _token_len(para) <= target:
                    current = para
                else:
                    chunks.extend(_split_sentences(para, target))
                    current = ""
        if current:
            chunks.append(current)
        return chunks

    return _split_sentences(text, target)


def _split_by_token_limit(text: str, max_tokens: int) -> list[str]:
    """Split text into segments each of at most max_tokens (no overlap)."""
    if not text.strip():
        return []
    tokens = _encoder.encode(text)
    if len(tokens) <= max_tokens:
        return [text] if text.strip() else []
    result: list[str] = []
    while len(tokens) > max_tokens:
        segment_tokens = tokens[:max_tokens]
        result.append(_encoder.decode(segment_tokens))
        tokens = tokens[max_tokens:]
    if tokens:
        result.append(_encoder.decode(tokens))
    return result


def _split_sentences(text: str, target: int) -> list[str]:
    """Split by sentence boundaries when paragraphs are too large."""
    sentences = _SENTENCE_PATTERN.split(text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if _token_len(candidate) <= target:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if _token_len(sentence) > CHUNK_MAX_TOKENS:
                sub_chunks = _split_by_token_limit(sentence, CHUNK_TARGET_TOKENS)
                chunks.extend(sub_chunks)
                current = ""
            else:
                current = sentence
    if current:
        chunks.append(current)
    return chunks


def _add_overlap(chunks: list[str]) -> list[str]:
    """Add token overlap between consecutive chunks."""
    if len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tokens = _encoder.encode(chunks[i - 1])
        overlap_tokens = prev_tokens[-CHUNK_OVERLAP_TOKENS:] if len(prev_tokens) > CHUNK_OVERLAP_TOKENS else prev_tokens
        overlap_text = _encoder.decode(overlap_tokens).strip()
        merged = f"{overlap_text} {chunks[i]}" if overlap_text else chunks[i]
        result.append(merged)
    return result


def chunk_markdown(markdown: str, page_url: str, source_url: str) -> list[Chunk]:
    """
    Chunk a markdown document into pieces suitable for embedding.

    Returns a list of Chunk dicts with keys: source_url, page_url, title, content.
    """
    sections = _split_by_headers(markdown)
    all_chunks: list[Chunk] = []

    for section in sections:
        raw_chunks = _split_to_target(section["text"], CHUNK_TARGET_TOKENS)
        overlapped = _add_overlap(raw_chunks)
        for content in overlapped:
            if content.strip():
                tokens = _encoder.encode(content)
                if len(tokens) > CHUNK_MAX_TOKENS:
                    content = _encoder.decode(tokens[:CHUNK_MAX_TOKENS])
                all_chunks.append({
                    "source_url": source_url,
                    "page_url": page_url,
                    "title": section["title"],
                    "content": content.strip(),
                })

    return all_chunks
