from datetime import date
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


class TestGithubTrending:
    def test_returns_trending_list(self, client: TestClient) -> None:
        """GET /recommendations/github-trending returns trending repos."""
        session = _make_session(
            [
                {
                    "repo_url": "https://github.com/octocat/Hello-World",
                    "data": {
                        "name": "Hello-World",
                        "full_name": "octocat/Hello-World",
                        "description": "A test repo",
                        "stargazers_count": 1500,
                        "language": "Go",
                    },
                    "stars_today": 200,
                    "trending_date": date(2026, 3, 12),
                    "linked_project_id": None,
                    "categoryId": None,
                    "domainId": None,
                },
            ]
        )
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get("/v1/recommendations/github-trending")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["repo_url"] == "https://github.com/octocat/Hello-World"
        assert data[0]["stars_today"] == 200
        assert data[0]["full_name"] == "octocat/Hello-World"
        assert data[0]["name"] == "Hello-World"

    def test_with_linked_project(self, client: TestClient) -> None:
        """LEFT JOIN enriches response when project exists in public.Project."""
        session = _make_session(
            [
                {
                    "repo_url": "https://github.com/octocat/Hello-World",
                    "data": {
                        "name": "Hello-World",
                        "full_name": "octocat/Hello-World",
                        "description": "A test repo",
                        "stargazers_count": 1500,
                        "language": "Go",
                    },
                    "stars_today": 200,
                    "trending_date": date(2026, 3, 12),
                    "linked_project_id": "abc-123",
                    "categoryId": "cat-1",
                    "domainId": "dom-1",
                },
            ]
        )
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get("/v1/recommendations/github-trending")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert data[0]["linked_project_id"] == "abc-123"
        assert data[0]["category_id"] == "cat-1"

    def test_respects_limit(self, client: TestClient) -> None:
        """GET /recommendations/github-trending?limit=5 limits results."""
        session = _make_session([])
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get("/v1/recommendations/github-trending?limit=5")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200

    def test_limit_validation(self, client: TestClient) -> None:
        """Limit must be between 1 and 50."""
        session = _make_session([])
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get("/v1/recommendations/github-trending?limit=0")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 422
