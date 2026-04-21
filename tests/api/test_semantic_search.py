from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def _make_pool(rows: list[dict]) -> MagicMock:
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows
    mock_pool = MagicMock()
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_pool


class TestSearchNatural:
    def test_requires_query(self, client: TestClient) -> None:
        response = client.get("/projects/search-natural")
        assert response.status_code == 422

    def test_empty_query_rejected(self, client: TestClient) -> None:
        response = client.get("/projects/search-natural?q=")
        assert response.status_code == 422

    def test_returns_ranked_projects(self, client: TestClient) -> None:
        from src.services.api.dependencies import get_pool
        from src.services.api.main import app

        pool = _make_pool(
            [
                {
                    "id": "p1",
                    "title": "MedicalGPT",
                    "description": "LLM for medical queries",
                    "repo_url": "https://github.com/org/medical-gpt",
                    "logo_url": None,
                    "similarity": 0.91,
                },
                {
                    "id": "p2",
                    "title": "RadiAI",
                    "description": "Radiology imaging assistant",
                    "repo_url": "https://github.com/org/radiai",
                    "logo_url": None,
                    "similarity": 0.82,
                },
            ]
        )
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get(
                "/projects/search-natural?q=medical+python+llm&limit=2"
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["title"] == "MedicalGPT"
        assert body[0]["similarity"] == 0.91
        assert body[1]["id"] == "p2"

    def test_hard_filters_apply(self, client: TestClient) -> None:
        """Verify filter params reach the SQL (cursor.execute called with them)."""
        from src.services.api.dependencies import get_pool
        from src.services.api.main import app

        pool = _make_pool([])
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get(
                "/projects/search-natural"
                "?q=medical&language=Python&domain=Healthcare&limit=5"
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        # The SQL text should mention filter joins
        call_args = (
            pool.get_cursor.return_value.__enter__.return_value.execute.call_args
        )
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "project_domain" in sql
        assert "tech_stack" in sql
        assert "Python" in params
        assert "Healthcare" in params
