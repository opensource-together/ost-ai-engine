from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.services.api.dependencies import get_pool
from src.services.api.main import app


def _make_result(
    *,
    rows: list[dict] | None = None,
    first: dict | None = None,
) -> MagicMock:
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows or []
    mock_result.mappings.return_value.first.return_value = first
    return mock_result


def _make_session(rows: list[dict]) -> MagicMock:
    """Create a mock session whose execute() returns one result set."""
    mock_session = MagicMock()
    mock_session.execute.return_value = _make_result(
        rows=rows,
        first=rows[0] if rows else None,
    )
    return mock_session


class TestSearchProjects:
    def test_search_with_query(self, client: TestClient) -> None:
        """GET /projects/search?q=react returns matching projects."""
        session = _make_session(
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
        app.dependency_overrides[get_pool] = lambda: session
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

    def test_search_with_filters_passes_category_to_sql(
        self, client: TestClient
    ) -> None:
        """GET /projects/search with category filter adds AND c.name = %s."""
        mock_session = MagicMock()
        mock_session.execute.return_value = _make_result(rows=[])

        app.dependency_overrides[get_pool] = lambda: mock_session
        try:
            response = client.get("/projects/search?q=test&category=Web+Development")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        sql = str(mock_session.execute.call_args[0][0])
        params = mock_session.execute.call_args[0][1]
        assert "AND c.name = :category" in sql
        assert params["category"] == "Web Development"

    def test_search_limit_over_max_returns_422(self, client: TestClient) -> None:
        """GET /projects/search?limit=100 returns 422 since limit exceeds max (50)."""
        session = _make_session([])
        app.dependency_overrides[get_pool] = lambda: session
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

        mock_session = MagicMock()
        mock_session.execute.side_effect = [
            _make_result(first=project_row),
            _make_result(rows=categories),
            _make_result(rows=domains),
            _make_result(rows=tech_stacks),
        ]

        app.dependency_overrides[get_pool] = lambda: mock_session
        try:
            response = client.get("/projects/550e8400-e29b-41d4-a716-446655440000")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My Project"
        assert data["categories"] == [{"id": "c1", "name": "Web"}]
        assert data["domains"] == [{"id": "d1", "name": "Finance"}]
        assert len(data["tech_stacks"]) == 1
        assert data["tech_stacks"][0]["name"] == "Python"

    def test_get_nonexistent_project_returns_404(self, client: TestClient) -> None:
        """GET /projects/{id} returns 404 for unknown ID."""
        mock_session = MagicMock()
        mock_session.execute.return_value = _make_result(first=None)

        app.dependency_overrides[get_pool] = lambda: mock_session
        try:
            response = client.get("/projects/550e8400-e29b-41d4-a716-446655440000")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 404


class TestFindSimilar:
    def test_find_similar_returns_list(self, client: TestClient) -> None:
        """GET /projects/{id}/similar returns similar projects."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = [
            _make_result(first={"vector": "[0.1, 0.2]"}),
            _make_result(
                rows=[
                    {
                        "id": "2",
                        "title": "Similar Project",
                        "description": "Desc",
                        "repo_url": "https://github.com/org/similar",
                        "similarity": 0.85,
                    },
                ]
            ),
        ]

        app.dependency_overrides[get_pool] = lambda: mock_session
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
        mock_session = MagicMock()
        mock_session.execute.return_value = _make_result(first=None)

        app.dependency_overrides[get_pool] = lambda: mock_session
        try:
            response = client.get(
                "/projects/550e8400-e29b-41d4-a716-446655440000/similar"
            )
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 404
