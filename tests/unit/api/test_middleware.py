"""Unit tests for security headers middleware."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from src.api.middleware import SecurityHeadersMiddleware


class TestSecurityHeadersMiddleware:
    def test_adds_hsts_when_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("API_ENABLE_HSTS", "true")
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/ping")
        def ping() -> dict[str, str]:
            return {"ok": "1"}

        response = TestClient(app).get("/ping")

        assert response.status_code == 200
        assert response.headers["Strict-Transport-Security"] == (
            "max-age=31536000; includeSubDomains"
        )
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
