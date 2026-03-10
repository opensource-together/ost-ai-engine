"""Contract tests ensuring API responses match the shape expected by ost-mcp OSTClient.

Each test verifies that the JSON response contains exactly the fields the MCP
TypeScript client expects (see ost-mcp/src/types.ts), with correct types.
"""

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# -- Expected fields per MCP type (from ost-mcp/src/types.ts) -----------------

CATEGORY_FIELDS = {"id": str, "name": str}
DOMAIN_FIELDS = {"id": str, "name": str}
TECHSTACK_FIELDS = {"id": str, "name": str, "icon_url": str, "type": str}
PROJECT_FIELDS = {
    "id": str,
    "title": str,
    "description": (str, type(None)),
    "repo_url": (str, type(None)),
    "published": bool,
    "trending": bool,
    "logo_url": (str, type(None)),
    "categories": list,
    "domains": list,
    "tech_stacks": list,
}
SIMILAR_PROJECT_FIELDS = {
    "id": str,
    "title": str,
    "description": (str, type(None)),
    "repo_url": (str, type(None)),
    "similarity": (int, float),
}
TRENDING_FIELDS = {
    "project_id": str,
    "stars": (int, type(None)),
    "last_synced_at": (str, type(None)),
}


def _assert_shape(obj: dict, fields: dict) -> None:
    """Assert that obj has exactly the expected keys with matching types."""
    assert set(obj.keys()) == set(fields.keys()), (
        f"Key mismatch: got {set(obj.keys())}, expected {set(fields.keys())}"
    )
    for key, expected_type in fields.items():
        assert isinstance(obj[key], expected_type), (
            f"Field '{key}': expected {expected_type}, got {type(obj[key])}"
        )


# -- Fixtures ------------------------------------------------------------------

FAKE_PROJECT_ROW = {
    "id": "proj-1",
    "title": "Test Project",
    "description": "A test project",
    "repo_url": "https://github.com/test/test",
    "published": True,
    "trending": False,
    "logo_url": None,
}

FAKE_CATEGORY_ROW = {"id": "cat-1", "name": "Web"}
FAKE_DOMAIN_ROW = {"id": "dom-1", "name": "Frontend"}
FAKE_TECHSTACK_ROW = {
    "id": "ts-1",
    "name": "React",
    "icon_url": "https://example.com/react.svg",
    "type": "framework",
}


@pytest.fixture()
def contract_client() -> Generator[TestClient, None, None]:
    """TestClient with mock DB returning realistic row data."""
    mock_pool = MagicMock()
    mock_cursor = MagicMock()
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None

    with (
        patch("src.services.api.dependencies._pool", mock_pool),
        patch("src.services.api.main._get_config") as mock_cfg,
        patch("src.services.api.dependencies.init_pool"),
    ):
        mock_cfg.return_value = MagicMock(
            database_url="postgresql://test:test@localhost:5432/test",
        )
        from src.services.api.main import app

        yield TestClient(app)

    # Store cursor ref for per-test configuration
    contract_client._mock_cursor = mock_cursor  # type: ignore[attr-defined]


@pytest.fixture()
def mock_cursor(contract_client: TestClient) -> MagicMock:
    """Access the mock cursor to configure return values per test."""
    pool = contract_client.app.dependency_overrides.get(None)
    # Get cursor from the patched pool
    with patch("src.services.api.dependencies._pool") as p:
        return p.get_cursor.return_value.__enter__.return_value


# -- Contract Tests ------------------------------------------------------------


class TestCategoryContract:
    """GET /categories must return Category[] shape."""

    def test_response_matches_mcp_category_type(
        self, contract_client: TestClient
    ) -> None:
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            cursor.fetchall.return_value = [FAKE_CATEGORY_ROW]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/categories")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        _assert_shape(data[0], CATEGORY_FIELDS)


class TestDomainContract:
    """GET /domains must return Domain[] shape."""

    def test_response_matches_mcp_domain_type(
        self, contract_client: TestClient
    ) -> None:
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            cursor.fetchall.return_value = [FAKE_DOMAIN_ROW]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/domains")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        _assert_shape(data[0], DOMAIN_FIELDS)


class TestTechStackContract:
    """GET /techstacks must return TechStack[] shape."""

    def test_response_matches_mcp_techstack_type(
        self, contract_client: TestClient
    ) -> None:
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            cursor.fetchall.return_value = [FAKE_TECHSTACK_ROW]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/techstacks")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        _assert_shape(data[0], TECHSTACK_FIELDS)


class TestProjectSearchContract:
    """GET /projects/search must return Project[] shape."""

    def test_response_matches_mcp_project_type(
        self, contract_client: TestClient
    ) -> None:
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            cursor.fetchall.return_value = [FAKE_PROJECT_ROW]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/projects/search?q=test")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        _assert_shape(data[0], PROJECT_FIELDS)

    def test_search_project_contains_nested_references(
        self, contract_client: TestClient
    ) -> None:
        """Verify categories/domains/tech_stacks are arrays (even if empty)."""
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            cursor.fetchall.return_value = [FAKE_PROJECT_ROW]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/projects/search?q=test")

        project = resp.json()[0]
        assert isinstance(project["categories"], list)
        assert isinstance(project["domains"], list)
        assert isinstance(project["tech_stacks"], list)


class TestProjectDetailContract:
    """GET /projects/{id} must return Project shape with nested references."""

    def test_response_matches_mcp_project_type_with_relations(
        self, contract_client: TestClient
    ) -> None:
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            # get_project makes 4 sequential queries
            cursor.fetchone.return_value = FAKE_PROJECT_ROW
            cursor.fetchall.side_effect = [
                [FAKE_CATEGORY_ROW],
                [FAKE_DOMAIN_ROW],
                [FAKE_TECHSTACK_ROW],
            ]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/projects/proj-1")

        assert resp.status_code == 200
        data = resp.json()
        _assert_shape(data, PROJECT_FIELDS)

        # Verify nested objects match their MCP types
        assert len(data["categories"]) == 1
        _assert_shape(data["categories"][0], CATEGORY_FIELDS)
        assert len(data["domains"]) == 1
        _assert_shape(data["domains"][0], DOMAIN_FIELDS)
        assert len(data["tech_stacks"]) == 1
        _assert_shape(data["tech_stacks"][0], TECHSTACK_FIELDS)


class TestSimilarContract:
    """GET /projects/{id}/similar must return SimilarProject[] shape."""

    def test_response_matches_mcp_similar_project_type(
        self, contract_client: TestClient
    ) -> None:
        similar_row = {
            "id": "proj-2",
            "title": "Similar Project",
            "description": "Another project",
            "repo_url": "https://github.com/test/similar",
            "similarity": 0.87,
        }
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            # First query: check embedding exists
            cursor.fetchone.return_value = {"vector": [0.1] * 384}
            # Second query: similar projects
            cursor.fetchall.return_value = [similar_row]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/projects/proj-1/similar")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        _assert_shape(data[0], SIMILAR_PROJECT_FIELDS)
        assert 0 <= data[0]["similarity"] <= 1


class TestTrendingContract:
    """GET /recommendations/trending must return TrendingProject[] shape."""

    def test_response_matches_mcp_trending_type(
        self, contract_client: TestClient
    ) -> None:
        trending_row = {
            "project_id": "proj-1",
            "stars": 1500,
            "last_synced_at": datetime(2025, 1, 15, tzinfo=UTC),
        }
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            cursor.fetchall.return_value = [trending_row]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/recommendations/trending")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        _assert_shape(data[0], TRENDING_FIELDS)

    def test_trending_with_null_fields(self, contract_client: TestClient) -> None:
        """MCP client must handle null stars and last_synced_at."""
        trending_row = {
            "project_id": "proj-2",
            "stars": None,
            "last_synced_at": None,
        }
        with patch("src.services.api.dependencies._pool") as mock_pool:
            cursor = MagicMock()
            cursor.fetchall.return_value = [trending_row]
            mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=cursor)
            mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            resp = contract_client.get("/recommendations/trending")

        data = resp.json()[0]
        assert data["stars"] is None
        assert data["last_synced_at"] is None
