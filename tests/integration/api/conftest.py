import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client_db() -> TestClient:
    """FastAPI TestClient against real DATABASE_URL."""
    assert os.environ.get("DATABASE_URL"), (
        "DATABASE_URL must be set for database-tier tests."
    )
    os.environ.setdefault("LINKER_SKIP_SEMANTIC_INIT", "true")
    os.environ.setdefault("OST_LINKER_REQUIRE_SERVICE_TOKEN", "false")

    from src.api.main import app

    with TestClient(app) as client:
        yield client
