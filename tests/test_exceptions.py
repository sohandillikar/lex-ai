"""
Tests for src.exceptions.
"""
from __future__ import annotations

import pytest

from src.exceptions import (
    ConfigurationError,
    CrawlError,
    DatabaseError,
    EmbeddingError,
    LexAIError,
    ValidationError,
)


class TestLexAIError:
    def test_message_and_hint(self):
        err = LexAIError("Something failed", hint="Try X")
        assert str(err) == "Something failed"
        assert err.message == "Something failed"
        assert err.hint == "Try X"

    def test_hint_optional(self):
        err = LexAIError("Just a message")
        assert err.hint is None


class TestSubclasses:
    def test_inheritance(self):
        assert issubclass(ValidationError, LexAIError)
        assert issubclass(ConfigurationError, LexAIError)
        assert issubclass(DatabaseError, LexAIError)
        assert issubclass(EmbeddingError, LexAIError)
        assert issubclass(CrawlError, LexAIError)

    def test_can_raise_and_catch(self):
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid input", hint="Check format")
        assert exc_info.value.message == "Invalid input"
        assert exc_info.value.hint == "Check format"
