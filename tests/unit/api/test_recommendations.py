from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.dependencies import get_db
from src.api.main import app


def _make_session(rows: list[dict]) -> MagicMock:
    """Create a mock session whose execute().mappings().all() returns rows."""
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    mock_session = MagicMock()
    mock_session.execute.return_value = mock_result
    return mock_session


class TestTrending:
    def test_get_trending_returns_list(self, client: TestClient) -> None:
        """GET /recommendations/trending returns trending projects."""
        session = _make_session(
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
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get("/v1/recommendations/trending")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["stars"] == 1500

    def test_get_trending_respects_limit(self, client: TestClient) -> None:
        """GET /recommendations/trending?limit=5 limits results."""
        session = _make_session([])
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get("/v1/recommendations/trending?limit=5")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
