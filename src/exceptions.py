"""
Custom exceptions for lex-ai.

Provides structured error types for clearer handling and user-facing messages.
"""
from __future__ import annotations


class LexAIError(Exception):
    """Base exception for lex-ai."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        self.message = message
        self.hint = hint
        super().__init__(message)


class ConfigurationError(LexAIError):
    """Raised when configuration is invalid or missing."""


class DatabaseError(LexAIError):
    """Raised when database operations fail."""


class EmbeddingError(LexAIError):
    """Raised when OpenAI embedding API fails."""


class CrawlError(LexAIError):
    """Raised when crawling or indexing fails."""


class ValidationError(LexAIError):
    """Raised when user input fails validation."""
