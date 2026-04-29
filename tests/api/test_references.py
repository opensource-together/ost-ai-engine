from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.services.api.dependencies import get_pool
from src.services.api.main import app


def _make_session(rows: list[dict]) -> MagicMock:
    """Create a mock session whose execute().mappings().all() returns rows."""
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    mock_session = MagicMock()
    mock_session.execute.return_value = mock_result
    return mock_session


class TestCategories:
    def test_list_categories_returns_list(self, client: TestClient) -> None:
        """GET /categories returns a list of categories."""
        session = _make_session(
            [
                {"id": "1", "name": "Web Development"},
                {"id": "2", "name": "Machine Learning"},
            ]
        )
        app.dependency_overrides[get_pool] = lambda: session
        try:
            response = client.get("/categories")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Web Development"


class TestDomains:
    def test_list_domains_returns_list(self, client: TestClient) -> None:
        """GET /domains returns a list of domains."""
        session = _make_session(
            [
                {"id": "1", "name": "Healthcare"},
            ]
        )
        app.dependency_overrides[get_pool] = lambda: session
        try:
            response = client.get("/domains")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestTechStacks:
    def test_list_techstacks_returns_list(self, client: TestClient) -> None:
        """GET /techstacks returns a list of tech stacks."""
        session = _make_session(
            [
                {
                    "id": "1",
                    "name": "Python",
                    "icon_url": "http://img",
                    "type": "LANGUAGE",
                },
            ]
        )
        app.dependency_overrides[get_pool] = lambda: session
        try:
            response = client.get("/techstacks")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        data = response.json()
        assert data[0]["type"] == "LANGUAGE"
