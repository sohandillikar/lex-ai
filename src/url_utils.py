"""
URL utilities for lex-ai.

Provides normalization, validation, and formatting for documentation URLs.
"""
from __future__ import annotations

import re
import urllib.request
from urllib.parse import urljoin, urlparse, urlunparse


# Basic URL validation pattern (scheme + netloc required)
_URL_PATTERN = re.compile(
    r"^https?://"  # scheme
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S*)$",
    re.IGNORECASE,
)


def normalize_source_url(url: str) -> str:
    """Extract scheme + netloc from a URL (e.g. https://docs.example.com/path -> https://docs.example.com)."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme or "https", parsed.netloc, "", "", "", ""))


def ensure_scheme(url: str, default: str = "https") -> str:
    """Ensure URL has http or https scheme. Defaults to https if missing."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return f"{default}://{url}"
    return url


def validate_url(url: str) -> tuple[bool, str | None]:
    """
    Validate that a string is a plausible HTTP/HTTPS URL.

    Returns:
        (is_valid, error_message). error_message is None when valid.
    """
    url = url.strip()
    if not url:
        return False, "URL is empty"

    url = ensure_scheme(url)
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid scheme: {parsed.scheme}. Use http or https."

    if not parsed.netloc:
        return False, "URL must have a host (e.g. docs.example.com)"

    if not _URL_PATTERN.match(url):
        return False, "URL format is invalid"

    return True, None


def is_valid_url(url: str) -> bool:
    """Convenience: return True if URL is valid."""
    valid, _ = validate_url(url)
    return valid


# Markdown link pattern: [text](url)
_MD_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def fetch_llms_txt_urls(base_url: str, max_urls: int = 50) -> list[str] | None:
    """
    Fetch llms.txt from a docs URL and extract doc page URLs.
    Returns list of URLs, or None if llms.txt not found.
    """
    base_url = base_url.rstrip("/")
    llms_url = f"{base_url}/llms.txt"
    try:
        with urllib.request.urlopen(llms_url, timeout=10) as resp:
            if resp.status != 200:
                return None
            text = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

    base_parsed = urlparse(base_url)
    base_netloc = base_parsed.netloc
    urls: list[str] = []
    seen: set[str] = set()

    for match in _MD_LINK_PATTERN.finditer(text):
        link_url = match.group(2).strip()
        if not link_url or link_url.startswith("#"):
            continue
        full_url = urljoin(base_url + "/", link_url)
        parsed = urlparse(full_url)
        if parsed.netloc != base_netloc:
            continue
        if full_url not in seen:
            seen.add(full_url)
            urls.append(full_url)
            if len(urls) >= max_urls:
                break

    return urls if urls else None
