from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.services.api.dependencies import get_pool
from src.services.api.main import app


def _make_pool(rows: list[dict]) -> MagicMock:
    """Create a mock pool whose cursor returns given rows."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows
    mock_pool = MagicMock()
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_pool


class TestTrending:
    def test_get_trending_returns_list(self, client: TestClient) -> None:
        """GET /recommendations/trending returns trending projects."""
        pool = _make_pool(
            [
                {
                    "project_id": "1",
                    "stars": 1500,
                    "last_synced_at": datetime(2026, 1, 1),
                },
                {
                    "project_id": "2",
                    "stars": 800,
                    "last_synced_at": datetime(2026, 1, 1),
                },
            ]
        )
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/recommendations/trending")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["stars"] == 1500

    def test_get_trending_respects_limit(self, client: TestClient) -> None:
        """GET /recommendations/trending?limit=5 limits results."""
        pool = _make_pool([])
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/recommendations/trending?limit=5")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
