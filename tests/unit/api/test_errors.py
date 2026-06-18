"""Unit tests for structured API error handlers."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient

from src.api.errors import register_error_handlers


class TestErrorHandlers:
    def test_rate_limit_error_uses_expected_code(self) -> None:
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/limited")
        def limited() -> None:
            raise HTTPException(status_code=429, detail="Too many requests")

        response = TestClient(app).get("/limited")

        assert response.status_code == 429
        assert response.json() == {
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Too many requests",
            }
        }
