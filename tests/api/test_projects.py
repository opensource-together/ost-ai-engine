from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.services.api.dependencies import get_pool
from src.services.api.main import app


def _make_pool(rows: list[dict]) -> MagicMock:
    """Create a mock pool whose cursor returns given rows."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows
    mock_cursor.fetchone.return_value = rows[0] if rows else None
    mock_pool = MagicMock()
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_pool


class TestSearchProjects:
    def test_search_with_query(self, client: TestClient) -> None:
        """GET /projects/search?q=react returns matching projects."""
        pool = _make_pool(
            [
                {
                    "id": "1",
                    "title": "React App",
                    "description": "A react app",
                    "repo_url": "https://github.com/org/react-app",
                    "published": True,
                    "trending": False,
                    "logo_url": None,
                },
            ]
        )
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/projects/search?q=react")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == "React App"

    def test_search_empty_query_returns_422(self, client: TestClient) -> None:
        """GET /projects/search without q returns 422 (validation error)."""
        response = client.get("/projects/search")
        assert response.status_code == 422

    def test_search_with_filters(self, client: TestClient) -> None:
        """GET /projects/search with category filter narrows results."""
        pool = _make_pool([])
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/projects/search?q=test&category=Web+Development")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200

    def test_search_limit_over_max_returns_422(self, client: TestClient) -> None:
        """GET /projects/search?limit=100 returns 422 since limit exceeds max (50)."""
        pool = _make_pool([])
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/projects/search?q=test&limit=100")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 422


class TestGetProject:
    def test_get_existing_project(self, client: TestClient) -> None:
        """GET /projects/{id} returns project details."""
        project_row = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "My Project",
            "description": "Desc",
            "repo_url": "https://github.com/org/repo",
            "published": True,
            "trending": False,
            "logo_url": None,
        }
        categories = [{"id": "c1", "name": "Web"}]
        domains = [{"id": "d1", "name": "Finance"}]
        tech_stacks = [
            {"id": "t1", "name": "Python", "icon_url": "http://img", "type": "LANGUAGE"}
        ]

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = project_row
        mock_cursor.fetchall.side_effect = [categories, domains, tech_stacks]
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        app.dependency_overrides[get_pool] = lambda: mock_pool
        try:
            response = client.get("/projects/550e8400-e29b-41d4-a716-446655440000")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        assert response.json()["title"] == "My Project"

    def test_get_nonexistent_project_returns_404(self, client: TestClient) -> None:
        """GET /projects/{id} returns 404 for unknown ID."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        app.dependency_overrides[get_pool] = lambda: mock_pool
        try:
            response = client.get("/projects/550e8400-e29b-41d4-a716-446655440000")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 404


class TestFindSimilar:
    def test_find_similar_returns_list(self, client: TestClient) -> None:
        """GET /projects/{id}/similar returns similar projects."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"vector": "[0.1, 0.2]"},
        ]
        mock_cursor.fetchall.return_value = [
            {
                "id": "2",
                "title": "Similar Project",
                "description": "Desc",
                "repo_url": "https://github.com/org/similar",
                "similarity": 0.85,
            },
        ]
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        app.dependency_overrides[get_pool] = lambda: mock_pool
        try:
            response = client.get(
                "/projects/550e8400-e29b-41d4-a716-446655440000/similar"
            )
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["similarity"] == 0.85

    def test_find_similar_no_embedding_returns_404(self, client: TestClient) -> None:
        """GET /projects/{id}/similar returns 404 when no embedding exists."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        app.dependency_overrides[get_pool] = lambda: mock_pool
        try:
            response = client.get(
                "/projects/550e8400-e29b-41d4-a716-446655440000/similar"
            )
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 404
