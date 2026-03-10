from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client with mocked DB pool."""
    mock_pool = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"?column?": 1}
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("src.services.api.dependencies._pool", mock_pool):
        with patch("src.services.api.main._get_config") as mock_cfg:
            mock_cfg.return_value = MagicMock(
                database_url="postgresql://test:test@localhost:5432/test",
            )
            with patch("src.services.api.dependencies.init_pool"):
                from src.services.api.main import app

                yield TestClient(app)
