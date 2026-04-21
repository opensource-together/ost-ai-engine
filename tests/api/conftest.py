from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client with mocked DB pool and semantic service."""
    mock_pool = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"?column?": 1}
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

    mock_semantic = MagicMock()
    mock_semantic.encode.return_value = [0.1] * 384

    with (
        patch("src.services.api.dependencies._pool", mock_pool),
        patch("src.services.api.dependencies._semantic", mock_semantic),
        patch("src.services.api.main._get_config") as mock_cfg,
        patch("src.services.api.dependencies.init_pool"),
        patch("src.services.api.dependencies.init_semantic"),
    ):

        mock_cfg.return_value = MagicMock(
            database_url="postgresql://test:test@localhost:5432/test",
        )
        from src.services.api.main import app

        yield TestClient(app)
