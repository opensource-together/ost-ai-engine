"""Env-driven SlowAPI rate limit string (aligned with API_RATE_LIMIT)."""

import pytest

from src.services.api.rate_limit import rate_limit_per_minute


class TestRateLimitPerMinute:
    def test_defaults_to_sixty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("API_RATE_LIMIT", "")
        assert rate_limit_per_minute() == "60/minute"

    def test_respects_positive_integer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("API_RATE_LIMIT", "120")
        assert rate_limit_per_minute() == "120/minute"

    def test_invalid_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("API_RATE_LIMIT", "not-a-number")
        assert rate_limit_per_minute() == "60/minute"

    def test_non_positive_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("API_RATE_LIMIT", "0")
        assert rate_limit_per_minute() == "60/minute"
