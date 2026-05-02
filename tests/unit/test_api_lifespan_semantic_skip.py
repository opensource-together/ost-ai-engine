"""Lifespan: LINKER_SKIP_SEMANTIC_INIT avoids eager semantic model load."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestLifespanSemanticSkipEnv:
    def test_when_skip_semantic_true_init_semantic_not_called(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LINKER_SKIP_SEMANTIC_INIT", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql://ci:ci@127.0.0.1:5432/ci")
        monkeypatch.setenv("OST_LINKER_REQUIRE_SERVICE_TOKEN", "false")
        monkeypatch.delenv("OST_LINKER_SERVICE_TOKEN", raising=False)

        stub_semantic = MagicMock()

        with (
            patch("src.services.api.main.init_db"),
            patch("src.services.api.main.init_semantic", stub_semantic),
            patch("src.services.api.main.close_db"),
        ):
            from src.services.api.main import app

            with TestClient(app):
                pass

        assert stub_semantic.call_count == 0

    def test_when_skip_semantic_unset_init_semantic_called_once(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("LINKER_SKIP_SEMANTIC_INIT", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql://ci:ci@127.0.0.1:5432/ci")
        monkeypatch.setenv("OST_LINKER_REQUIRE_SERVICE_TOKEN", "false")
        monkeypatch.delenv("OST_LINKER_SERVICE_TOKEN", raising=False)

        stub_semantic = MagicMock()

        with (
            patch("src.services.api.main.init_db"),
            patch("src.services.api.main.init_semantic", stub_semantic),
            patch("src.services.api.main.close_db"),
        ):
            from src.services.api.main import app

            with TestClient(app):
                pass

        assert stub_semantic.call_count == 1
