from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client with mocked DB session factory and semantic service."""
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = {"?column?": 1}
    mock_result.mappings.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    mock_semantic = MagicMock()
    mock_semantic.encode.return_value = [0.1] * 384

    with (
        patch("src.api.dependencies._session_factory", MagicMock(return_value=mock_db)),
        patch("src.api.dependencies._semantic", mock_semantic),
        patch("src.api.main._get_config") as mock_cfg,
        patch("src.api.dependencies.init_db"),
        patch("src.api.dependencies.init_semantic"),
    ):

        mock_cfg.return_value = MagicMock(
            database_url="postgresql://test:test@localhost:5432/test",
            require_service_token=False,
            service_token=None,
        )
        from src.api.main import app

        yield TestClient(app)
