"""Live auth checks against real DATABASE_URL."""

import pytest


class TestAuthLive:
    def test_protected_route_requires_token_when_configured(
        self,
        client_db,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", "live-test-token")
        response = client_db.get("/v1/references/categories")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"

        ok = client_db.get(
            "/v1/references/categories",
            headers={"X-Service-Token": "live-test-token"},
        )
        assert ok.status_code == 200
