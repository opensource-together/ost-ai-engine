from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_pool
from src.api.main import app

pytestmark = pytest.mark.unit


def _make_pool(
    *,
    fetchall_rows: list[dict] | None = None,
    fetchone_rows: list[dict | None] | None = None,
) -> MagicMock:
    """Create a mock session whose execute() returns configured result mappings."""
    mock_session = MagicMock()

    def _make_result(
        *,
        rows: list[dict] | None = None,
        first: dict | None = None,
    ) -> MagicMock:
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = rows or []
        mock_result.mappings.return_value.first.return_value = first
        return mock_result

    if fetchone_rows is not None:
        execute_results = [
            _make_result(first=row) for row in fetchone_rows
        ]
        if fetchall_rows is not None:
            execute_results.append(_make_result(rows=fetchall_rows))
        mock_session.execute.side_effect = execute_results
    else:
        mock_session.execute.return_value = _make_result(rows=fetchall_rows)

    return mock_session


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
            response = client.get("/v1/projects/search?q=foo")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200


class TestServiceTokenEnforced:
    @pytest.mark.parametrize(
        "path",
        [
            "/v1/projects/search?q=foo",
            "/v1/projects/550e8400-e29b-41d4-a716-446655440000",
            "/v1/projects/550e8400-e29b-41d4-a716-446655440000/similar",
            "/v1/recommendations/trending",
            "/v1/references/categories",
            "/v1/references/domains",
            "/v1/references/techstacks",
        ],
    )
    def test_missing_header(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch, path: str
    ) -> None:
        """Protected endpoints return 401 without a service token header."""
        monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", "expected-token")

        response = client.get(path)

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"

    def test_mismatched_header(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Protected endpoints return 401 for the wrong service token."""
        monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", "expected-token")

        response = client.get(
            "/v1/projects/search?q=foo",
            headers={"X-Service-Token": "wrong-token"},
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"

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
                "/v1/projects/search?q=foo",
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


def test_strict_service_token_without_secret_fails_at_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When strict mode is on, startup fails if OST_LINKER_SERVICE_TOKEN is unset."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("OST_LINKER_REQUIRE_SERVICE_TOKEN", "true")
    monkeypatch.delenv("OST_LINKER_SERVICE_TOKEN", raising=False)
    with (
        patch("src.api.main.init_db"),
        patch("src.api.main.init_semantic"),
    ):
        with pytest.raises(RuntimeError, match="OST_LINKER_REQUIRE_SERVICE_TOKEN"):
            with TestClient(app):
                pass
