"""Unit tests for centralized logging."""

from __future__ import annotations

import logging

from src.core.logging import configure_logging, get_logger


class TestConfigureLogging:
    def test_configure_logging_is_idempotent(self) -> None:
        configure_logging()
        handler_count = len(logging.getLogger().handlers)
        configure_logging()
        assert len(logging.getLogger().handlers) == handler_count

    def test_get_logger_returns_named_logger(self) -> None:
        logger = get_logger("tests.logging")
        assert logger.name == "tests.logging"

    def test_json_formatter_when_env_set(self, monkeypatch) -> None:
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        monkeypatch.setenv("LOG_FORMAT", "json")
        configure_logging()
        assert root.handlers
        assert root.handlers[0].formatter is not None

    def test_text_formatter_by_default(self, monkeypatch) -> None:
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        configure_logging()
        formatter = root.handlers[0].formatter
        assert formatter is not None
        assert formatter.__class__.__name__ == "Formatter"
