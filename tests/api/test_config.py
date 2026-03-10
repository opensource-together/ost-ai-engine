import pytest

from src.services.api.config import APIConfig


class TestAPIConfig:
    def test_loads_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config loads with sensible defaults when only DATABASE_URL is set."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
        cfg = APIConfig()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8000
        assert cfg.rate_limit == 60

    def test_missing_database_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config raises ValidationError when DATABASE_URL is missing."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(Exception):
            APIConfig()
