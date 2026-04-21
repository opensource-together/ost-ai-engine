from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.services.api.dependencies import get_pool
from src.services.api.main import app

pytestmark = pytest.mark.api


def _make_pool(
    *,
    fetchall_rows: list[dict] | None = None,
    fetchone_rows: list[dict | None] | None = None,
) -> MagicMock:
    """Create a mock pool whose cursor returns the given rows."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = fetchall_rows or []
    if fetchone_rows is not None:
        mock_cursor.fetchone.side_effect = fetchone_rows
    else:
        mock_cursor.fetchone.return_value = None

    mock_pool = MagicMock()
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_pool


class TestServiceTokenOpen:
    def test_open_mode_allows_requests_without_header(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Protected endpoints stay open when no service token is configured."""
        monkeypatch.delenv("OST_LINKER_SERVICE_TOKEN", raising=False)
        pool = _make_pool(
            fetchall_rows=[
                {
                    "id": "1",
                    "title": "React App",
                    "description": "A react app",
                    "repo_url": "https://github.com/org/react-app",
                    "published": True,
                    "trending": False,
                    "logo_url": None,
                }
            ]
        )
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/projects/search?q=foo")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200


class TestServiceTokenEnforced:
    @pytest.mark.parametrize(
        "path",
        [
            "/projects/search?q=foo",
            "/projects/550e8400-e29b-41d4-a716-446655440000",
            "/projects/550e8400-e29b-41d4-a716-446655440000/similar",
            "/recommendations/trending",
            "/categories",
            "/domains",
            "/techstacks",
        ],
    )
    def test_missing_header(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch, path: str
    ) -> None:
        """Protected endpoints return 401 without a service token header."""
        monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", "expected-token")

        response = client.get(path)

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid or missing service token"}

    def test_mismatched_header(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Protected endpoints return 401 for the wrong service token."""
        monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", "expected-token")

        response = client.get(
            "/projects/search?q=foo",
            headers={"X-Service-Token": "wrong-token"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid or missing service token"}

    def test_matching_header(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Protected endpoints allow requests with the matching service token."""
        monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", "expected-token")
        pool = _make_pool(
            fetchall_rows=[
                {
                    "id": "1",
                    "title": "React App",
                    "description": "A react app",
                    "repo_url": "https://github.com/org/react-app",
                    "published": True,
                    "trending": False,
                    "logo_url": None,
                }
            ]
        )
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get(
                "/projects/search?q=foo",
                headers={"X-Service-Token": "expected-token"},
            )
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200


class TestHealthOpen:
    @pytest.mark.parametrize("service_token", [None, "expected-token"])
    def test_health_stays_open(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        service_token: str | None,
    ) -> None:
        """Health remains open whether service-token auth is enabled or not."""
        if service_token is None:
            monkeypatch.delenv("OST_LINKER_SERVICE_TOKEN", raising=False)
        else:
            monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", service_token)

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
