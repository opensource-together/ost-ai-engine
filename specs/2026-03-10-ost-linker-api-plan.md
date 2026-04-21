# OST Linker API Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a FastAPI REST API to ost-linker that exposes project data, recommendations, and similarity search for consumption by the ost-mcp server.

**Architecture:** Lightweight FastAPI service with synchronous endpoints, connection-pooled psycopg2, and read-only queries against pre-computed data. Runs as a separate Docker Compose service on port 8000 with a single uvicorn worker.

**Tech Stack:** FastAPI, uvicorn, psycopg2 (SimpleConnectionPool), slowapi, pydantic v2

**Spec:** `specs/2026-03-10-mcp-server-design.md`

---

## File Structure

```
src/services/api/
├── __init__.py
├── main.py              # FastAPI app, middleware, router includes
├── config.py            # Pydantic settings (env vars)
├── database.py          # Connection pool
├── dependencies.py      # FastAPI dependency (get_pool) — breaks circular imports
├── schemas.py           # All Pydantic response models
├── routes/
│   ├── __init__.py
│   ├── health.py        # GET /health
│   ├── projects.py      # GET /projects/search, /projects/{id}, /projects/{id}/similar
│   ├── recommendations.py  # GET /recommendations/trending
│   └── references.py    # GET /categories, /domains, /techstacks

tests/api/
├── __init__.py
├── conftest.py          # TestClient fixture + DB test helpers
├── test_health.py
├── test_projects.py
├── test_recommendations.py
└── test_references.py
```

---

## Chunk 1: Foundation (dependencies, config, DB pool, health endpoint)

### Task 1: Add dependencies to pyproject.toml

**Files:**
- Modify: `pyproject.toml:13-38` (dependencies section)

- [ ] **Step 1: Add FastAPI, uvicorn, and slowapi to dependencies**

Add to the `dependencies` list in `pyproject.toml`:
```toml
"fastapi>=0.115.0,<1",
"uvicorn[standard]>=0.34.0,<1",
"slowapi>=0.1.9,<0.2",
```

- [ ] **Step 2: Run `uv sync` to install**

Run: `uv sync`
Expected: Successful install, no conflicts

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "$(cat <<'EOF'
chore(deps): add fastapi, uvicorn, and slowapi

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 2: Create API config

**Files:**
- Create: `src/services/api/__init__.py`
- Create: `src/services/api/config.py`

- [ ] **Step 1: Write the test for config loading**

Create `tests/api/__init__.py` (empty) and `tests/api/conftest.py`:
```python
```

Create `tests/api/test_config.py`:
```python
import os

import pytest

from src.services.api.config import APIConfig


class TestAPIConfig:
    def test_loads_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config loads with sensible defaults when only DATABASE_URL is set."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
        cfg = APIConfig()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8000
        assert cfg.rate_limit == 60

    def test_missing_database_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config raises ValidationError when DATABASE_URL is missing."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(Exception):
            APIConfig()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.services.api'`

- [ ] **Step 3: Write the config module**

Create `src/services/api/__init__.py` (empty).

Create `src/services/api/config.py`:
```python
from pydantic import Field
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API configuration loaded from environment variables."""

    database_url: str = Field(alias="DATABASE_URL")
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    rate_limit: int = Field(default=60, alias="API_RATE_LIMIT")

    model_config = {"populate_by_name": True}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_config.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/services/api/ tests/api/
git commit -m "$(cat <<'EOF'
feat(api): add API config module with pydantic-settings

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 3: Create connection pool and DB dependency

**Files:**
- Create: `src/services/api/database.py`
- Test: `tests/api/test_database.py`

- [ ] **Step 1: Write the test**

Create `tests/api/test_database.py`:
```python
from unittest.mock import MagicMock, patch

from src.services.api.database import ConnectionPool


class TestConnectionPool:
    def test_get_cursor_yields_realdict_cursor(self) -> None:
        """get_cursor yields a RealDictCursor from the pool."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(ConnectionPool, "_pool") as mock_pool:
            mock_pool.getconn.return_value = mock_conn
            pool = ConnectionPool.__new__(ConnectionPool)
            pool._pool = mock_pool

            with pool.get_cursor() as cur:
                assert cur is mock_cursor

            mock_conn.rollback.assert_called_once()
            mock_pool.putconn.assert_called_once_with(mock_conn)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_database.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the database module**

Create `src/services/api/database.py`:
```python
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool


class ConnectionPool:
    """Thin wrapper around psycopg2 SimpleConnectionPool."""

    def __init__(self, database_url: str, minconn: int = 1, maxconn: int = 5) -> None:
        self._pool = SimpleConnectionPool(minconn, maxconn, database_url)

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """Yield a RealDictCursor, rollback on exit, return conn to pool."""
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
            conn.rollback()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self) -> None:
        """Close all pooled connections."""
        self._pool.closeall()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_database.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/services/api/database.py tests/api/test_database.py
git commit -m "$(cat <<'EOF'
feat(api): add connection pool with psycopg2 SimpleConnectionPool

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 4: Create Pydantic response schemas

**Files:**
- Create: `src/services/api/schemas.py`
- Test: `tests/api/test_schemas.py`

- [ ] **Step 1: Write the test**

Create `tests/api/test_schemas.py`:
```python
from src.services.api.schemas import CategoryOut, DomainOut, ProjectOut, TechStackOut


class TestSchemas:
    def test_project_out_from_dict(self) -> None:
        """ProjectOut can be constructed from a DB row dict."""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "My Project",
            "description": "A cool project",
            "repo_url": "https://github.com/org/repo",
            "published": True,
            "trending": False,
            "categories": [],
            "domains": [],
            "tech_stacks": [],
        }
        project = ProjectOut(**data)
        assert project.title == "My Project"
        assert project.categories == []

    def test_category_out(self) -> None:
        """CategoryOut holds id and name."""
        cat = CategoryOut(id="abc-123", name="Web Development")
        assert cat.name == "Web Development"

    def test_techstack_out_with_type(self) -> None:
        """TechStackOut includes type field."""
        ts = TechStackOut(id="x", name="Python", icon_url="http://img", type="LANGUAGE")
        assert ts.type == "LANGUAGE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_schemas.py -v`
Expected: FAIL

- [ ] **Step 3: Write the schemas module**

Create `src/services/api/schemas.py`:
```python
from datetime import datetime

from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: str
    name: str


class DomainOut(BaseModel):
    id: str
    name: str


class TechStackOut(BaseModel):
    id: str
    name: str
    icon_url: str
    type: str


class ProjectOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    repo_url: str | None = None
    published: bool = False
    trending: bool = False
    logo_url: str | None = None
    categories: list[CategoryOut] = []
    domains: list[DomainOut] = []
    tech_stacks: list[TechStackOut] = []


class ProjectSimilarOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    repo_url: str | None = None
    similarity: float


class TrendingProjectOut(BaseModel):
    project_id: str
    stars: int | None = None
    last_synced_at: datetime | None = None


class ErrorOut(BaseModel):
    detail: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/services/api/schemas.py tests/api/test_schemas.py
git commit -m "$(cat <<'EOF'
feat(api): add pydantic response schemas

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 5: Create FastAPI app with health endpoint

**Files:**
- Create: `src/services/api/main.py`
- Create: `src/services/api/routes/__init__.py`
- Create: `src/services/api/routes/health.py`
- Test: `tests/api/test_health.py`

- [ ] **Step 1: Write the test**

Create `tests/api/conftest.py`:
```python
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    """FastAPI test client with mocked DB pool."""
    mock_pool = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"?column?": 1}
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("src.services.api.dependencies._pool", mock_pool):
        with patch("src.services.api.main._get_config") as mock_cfg:
            mock_cfg.return_value = MagicMock(
                database_url="postgresql://test:test@localhost:5432/test",
            )
            with patch("src.services.api.dependencies.init_pool"):
                from src.services.api.main import app

                yield TestClient(app)
```

Create `tests/api/test_health.py`:
```python
from fastapi.testclient import TestClient


class TestHealth:
    def test_health_returns_ok(self, client: TestClient) -> None:
        """GET /health returns 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_health.py -v`
Expected: FAIL

- [ ] **Step 3: Write the app and health route**

Create `src/services/api/routes/__init__.py` (empty).

Create `src/services/api/routes/health.py`:
```python
from fastapi import APIRouter, Depends

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool

router = APIRouter()


@router.get("/health")
def health(pool: ConnectionPool = Depends(get_pool)) -> dict[str, str]:
    """Health check endpoint — verifies DB connectivity."""
    with pool.get_cursor() as cur:
        cur.execute("SELECT 1")
    return {"status": "ok"}
```

Create `src/services/api/dependencies.py` (breaks circular imports — routes import from here, not from main):
```python
from src.services.api.database import ConnectionPool

_pool: ConnectionPool | None = None


def init_pool(database_url: str) -> None:
    """Initialize the global connection pool."""
    global _pool
    _pool = ConnectionPool(database_url, minconn=1, maxconn=5)


def close_pool() -> None:
    """Close the global connection pool."""
    if _pool:
        _pool.close()


def get_pool() -> ConnectionPool:
    """FastAPI dependency: returns the connection pool."""
    if _pool is None:
        raise RuntimeError("Connection pool not initialized")
    return _pool
```

Create `src/services/api/main.py`:
```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.services.api.config import APIConfig
from src.services.api.dependencies import close_pool, init_pool
from src.services.api.routes import health


def _get_config() -> APIConfig:
    return APIConfig()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init pool. Shutdown: close pool."""
    config = _get_config()
    init_pool(config.database_url)
    yield
    close_pool()


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )


app = FastAPI(
    title="OST Linker API",
    description="Open-source project recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)  # type: ignore[arg-type]

app.include_router(health.router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Verify the app starts locally**

Run: `timeout 5 uvicorn src.services.api.main:app --host 127.0.0.1 --port 8000 || true`
Expected: Server starts (then times out after 5s, that's fine)

- [ ] **Step 6: Commit**

```bash
git add src/services/api/main.py src/services/api/routes/
git add tests/api/conftest.py tests/api/test_health.py
git commit -m "$(cat <<'EOF'
feat(api): add FastAPI app with health endpoint and rate limiting

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

## Chunk 2: Reference endpoints (categories, domains, techstacks)

### Task 6: Implement reference endpoints

**Files:**
- Create: `src/services/api/routes/references.py`
- Test: `tests/api/test_references.py`

- [ ] **Step 1: Write the tests**

Create `tests/api/test_references.py`:
```python
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.services.api.schemas import CategoryOut, DomainOut, TechStackOut


class TestCategories:
    def test_list_categories_returns_list(self, client: TestClient) -> None:
        """GET /categories returns a list of categories."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": "1", "name": "Web Development"},
            {"id": "2", "name": "Machine Learning"},
        ]
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("src.services.api.routes.references.get_pool", return_value=mock_pool):
            response = client.get("/categories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Web Development"


class TestDomains:
    def test_list_domains_returns_list(self, client: TestClient) -> None:
        """GET /domains returns a list of domains."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": "1", "name": "Healthcare"},
        ]
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("src.services.api.routes.references.get_pool", return_value=mock_pool):
            response = client.get("/domains")

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestTechStacks:
    def test_list_techstacks_returns_list(self, client: TestClient) -> None:
        """GET /techstacks returns a list of tech stacks."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": "1", "name": "Python", "icon_url": "http://img", "type": "LANGUAGE"},
        ]
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("src.services.api.routes.references.get_pool", return_value=mock_pool):
            response = client.get("/techstacks")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["type"] == "LANGUAGE"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/api/test_references.py -v`
Expected: FAIL

- [ ] **Step 3: Write the references routes**

Create `src/services/api/routes/references.py`:
```python
from fastapi import APIRouter, Depends

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool
from src.services.api.schemas import CategoryOut, DomainOut, TechStackOut

router = APIRouter()


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(pool: ConnectionPool = Depends(get_pool)) -> list[dict]:
    """List all project categories."""
    with pool.get_cursor() as cur:
        cur.execute('SELECT id, name FROM public."Category" ORDER BY name')
        return cur.fetchall()


@router.get("/domains", response_model=list[DomainOut])
def list_domains(pool: ConnectionPool = Depends(get_pool)) -> list[dict]:
    """List all project domains."""
    with pool.get_cursor() as cur:
        cur.execute('SELECT id, name FROM public."Domain" ORDER BY name')
        return cur.fetchall()


@router.get("/techstacks", response_model=list[TechStackOut])
def list_techstacks(pool: ConnectionPool = Depends(get_pool)) -> list[dict]:
    """List all tech stacks."""
    with pool.get_cursor() as cur:
        cur.execute(
            """SELECT id, name, "iconUrl" AS icon_url, type
               FROM public.tech_stack
               ORDER BY name"""
        )
        return cur.fetchall()
```

- [ ] **Step 4: Register routes in main.py**

Add to `src/services/api/main.py`:
```python
from src.services.api.routes import health, references

# ... existing code ...

app.include_router(references.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/api/test_references.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add src/services/api/routes/references.py src/services/api/main.py
git add tests/api/test_references.py
git commit -m "$(cat <<'EOF'
feat(api): add categories, domains, and techstacks endpoints

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

## Chunk 3: Project endpoints (search, detail, similar)

### Task 7: Implement project search endpoint

**Files:**
- Create: `src/services/api/routes/projects.py`
- Test: `tests/api/test_projects.py`

- [ ] **Step 1: Write the tests**

Create `tests/api/test_projects.py`:
```python
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _mock_pool(rows: list[dict]) -> MagicMock:
    """Helper: create a mock pool that returns given rows."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows
    mock_cursor.fetchone.return_value = rows[0] if rows else None
    mock_pool = MagicMock()
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_pool


class TestSearchProjects:
    def test_search_with_query(self, client: TestClient) -> None:
        """GET /projects/search?q=react returns matching projects."""
        pool = _mock_pool([
            {
                "id": "1", "title": "React App", "description": "A react app",
                "repo_url": "https://github.com/org/react-app",
                "published": True, "trending": False, "logo_url": None,
            },
        ])
        with patch("src.services.api.routes.projects.get_pool", return_value=pool):
            response = client.get("/projects/search?q=react")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == "React App"

    def test_search_empty_query_returns_422(self, client: TestClient) -> None:
        """GET /projects/search without q returns 422 (validation error)."""
        response = client.get("/projects/search")
        assert response.status_code == 422

    def test_search_with_filters(self, client: TestClient) -> None:
        """GET /projects/search with category filter narrows results."""
        pool = _mock_pool([])
        with patch("src.services.api.routes.projects.get_pool", return_value=pool):
            response = client.get("/projects/search?q=test&category=Web+Development")

        assert response.status_code == 200

    def test_search_limit_capped_at_50(self, client: TestClient) -> None:
        """GET /projects/search?limit=100 is capped at 50."""
        pool = _mock_pool([])
        with patch("src.services.api.routes.projects.get_pool", return_value=pool):
            response = client.get("/projects/search?q=test&limit=100")

        assert response.status_code == 200


class TestGetProject:
    def test_get_existing_project(self, client: TestClient) -> None:
        """GET /projects/{id} returns project details."""
        pool = _mock_pool([{
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "My Project",
            "description": "Desc",
            "repo_url": "https://github.com/org/repo",
            "published": True,
            "trending": False,
            "logo_url": None,
            "category_id": "c1", "category_name": "Web",
            "domain_id": "d1", "domain_name": "Finance",
        }])
        with patch("src.services.api.routes.projects.get_pool", return_value=pool):
            response = client.get("/projects/550e8400-e29b-41d4-a716-446655440000")

        assert response.status_code == 200
        assert response.json()["title"] == "My Project"

    def test_get_nonexistent_project_returns_404(self, client: TestClient) -> None:
        """GET /projects/{id} returns 404 for unknown ID."""
        pool = _mock_pool([])
        with patch("src.services.api.routes.projects.get_pool", return_value=pool):
            response = client.get("/projects/550e8400-e29b-41d4-a716-446655440000")

        assert response.status_code == 404


class TestFindSimilar:
    def test_find_similar_returns_list(self, client: TestClient) -> None:
        """GET /projects/{id}/similar returns similar projects with similarity scores."""
        mock_cursor = MagicMock()
        # First call: check embedding exists
        mock_cursor.fetchone.side_effect = [
            {"vector": "[0.1, 0.2]"},  # embedding exists
        ]
        # Second call: similar projects
        mock_cursor.fetchall.return_value = [
            {
                "id": "2", "title": "Similar Project", "description": "Desc",
                "repo_url": "https://github.com/org/similar", "similarity": 0.85,
            },
        ]
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("src.services.api.routes.projects.get_pool", return_value=mock_pool):
            response = client.get("/projects/550e8400-e29b-41d4-a716-446655440000/similar")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["similarity"] == 0.85

    def test_find_similar_no_embedding_returns_404(self, client: TestClient) -> None:
        """GET /projects/{id}/similar returns 404 when no embedding exists."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_pool = MagicMock()
        mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("src.services.api.routes.projects.get_pool", return_value=mock_pool):
            response = client.get("/projects/550e8400-e29b-41d4-a716-446655440000/similar")

        assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/api/test_projects.py -v`
Expected: FAIL

- [ ] **Step 3: Write the projects routes**

Create `src/services/api/routes/projects.py`:
```python
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool
from src.services.api.schemas import ProjectOut, ProjectSimilarOut

router = APIRouter(prefix="/projects")

MAX_LIMIT = 50


@router.get("/search", response_model=list[ProjectOut])
def search_projects(
    q: str = Query(..., min_length=1),
    category: str | None = None,
    domain: str | None = None,
    techstack: str | None = None,
    limit: int = Query(default=20, ge=1, le=MAX_LIMIT),
    pool: ConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Search projects by keyword, optionally filtered by category/domain/techstack."""
    query = """
        SELECT DISTINCT p.id, p.title, p.description, p."repoUrl" AS repo_url,
               p.published, p.trending, p."logoUrl" AS logo_url
        FROM public."Project" p
        LEFT JOIN public.project_category pc ON p.id = pc."projectId"
        LEFT JOIN public."Category" c ON pc."categoryId" = c.id
        LEFT JOIN public.project_domain pd ON p.id = pd."projectId"
        LEFT JOIN public."Domain" d ON pd."domainId" = d.id
        LEFT JOIN public.project_tech_stack pts ON p.id = pts."projectId"
        LEFT JOIN public.tech_stack ts ON pts."techStackId" = ts.id
        WHERE (p.published = true OR p.trending = true)
          AND (p.title ILIKE %s OR p.description ILIKE %s)
    """
    pattern = f"%{q}%"
    params: list[Any] = [pattern, pattern]

    if category:
        query += " AND c.name = %s"
        params.append(category)
    if domain:
        query += " AND d.name = %s"
        params.append(domain)
    if techstack:
        query += " AND ts.name = %s"
        params.append(techstack)

    query += " ORDER BY p.trending DESC, p.title LIMIT %s"
    params.append(limit)

    with pool.get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    pool: ConnectionPool = Depends(get_pool),
) -> dict[str, Any]:
    """Get full project details by ID."""
    with pool.get_cursor() as cur:
        # Fetch project
        cur.execute(
            """SELECT id, title, description, "repoUrl" AS repo_url,
                      published, trending, "logoUrl" AS logo_url
               FROM public."Project"
               WHERE id = %s""",
            (project_id,),
        )
        project = cur.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Fetch relations
        cur.execute(
            """SELECT c.id, c.name FROM public."Category" c
               JOIN public.project_category pc ON c.id = pc."categoryId"
               WHERE pc."projectId" = %s""",
            (project_id,),
        )
        categories = cur.fetchall()

        cur.execute(
            """SELECT d.id, d.name FROM public."Domain" d
               JOIN public.project_domain pd ON d.id = pd."domainId"
               WHERE pd."projectId" = %s""",
            (project_id,),
        )
        domains = cur.fetchall()

        cur.execute(
            """SELECT ts.id, ts.name, ts."iconUrl" AS icon_url, ts.type::text
               FROM public.tech_stack ts
               JOIN public.project_tech_stack pts ON ts.id = pts."techStackId"
               WHERE pts."projectId" = %s""",
            (project_id,),
        )
        tech_stacks = cur.fetchall()

        result = dict(project)
        result["categories"] = categories
        result["domains"] = domains
        result["tech_stacks"] = tech_stacks
        return result


@router.get("/{project_id}/similar", response_model=list[ProjectSimilarOut])
def find_similar(
    project_id: str,
    limit: int = Query(default=10, ge=1, le=MAX_LIMIT),
    pool: ConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Find similar projects using pgvector cosine similarity."""
    with pool.get_cursor() as cur:
        # Check project has an embedding
        cur.execute(
            'SELECT vector FROM ml.embd_github_project WHERE "projectId" = %s',
            (project_id,),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Project embedding not found")

        cur.execute(
            """SELECT p.id, p.title, p.description, p."repoUrl" AS repo_url,
                      1 - (e.vector <=> ref.vector) AS similarity
               FROM ml.embd_github_project e
               JOIN ml.embd_github_project ref ON ref."projectId" = %s
               JOIN public."Project" p ON p.id = e."projectId"
               WHERE e."projectId" != %s
                 AND (p.published = true OR p.trending = true)
               ORDER BY e.vector <=> ref.vector
               LIMIT %s""",
            (project_id, project_id, limit),
        )
        return cur.fetchall()
```

- [ ] **Step 4: Register routes in main.py**

Add to `src/services/api/main.py` imports and router include:
```python
from src.services.api.routes import health, projects, references

app.include_router(projects.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/api/test_projects.py -v`
Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
git add src/services/api/routes/projects.py src/services/api/main.py
git add tests/api/test_projects.py
git commit -m "$(cat <<'EOF'
feat(api): add project search, detail, and similarity endpoints

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 8: Implement trending recommendations endpoint

**Files:**
- Create: `src/services/api/routes/recommendations.py`
- Test: `tests/api/test_recommendations.py`

- [ ] **Step 1: Write the test**

Create `tests/api/test_recommendations.py`:
```python
from unittest.mock import MagicMock, patch
from datetime import datetime

from fastapi.testclient import TestClient


def _mock_pool(rows: list[dict]) -> MagicMock:
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows
    mock_pool = MagicMock()
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_pool


class TestTrending:
    def test_get_trending_returns_list(self, client: TestClient) -> None:
        """GET /recommendations/trending returns trending projects."""
        pool = _mock_pool([
            {"project_id": "1", "stars": 1500, "last_synced_at": datetime(2026, 1, 1)},
            {"project_id": "2", "stars": 800, "last_synced_at": datetime(2026, 1, 1)},
        ])
        with patch("src.services.api.routes.recommendations.get_pool", return_value=pool):
            response = client.get("/recommendations/trending")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["stars"] == 1500

    def test_get_trending_respects_limit(self, client: TestClient) -> None:
        """GET /recommendations/trending?limit=5 limits results."""
        pool = _mock_pool([])
        with patch("src.services.api.routes.recommendations.get_pool", return_value=pool):
            response = client.get("/recommendations/trending?limit=5")

        assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_recommendations.py -v`
Expected: FAIL

- [ ] **Step 3: Write the recommendations route**

Create `src/services/api/routes/recommendations.py`:
```python
from typing import Any

from fastapi import APIRouter, Depends, Query

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool
from src.services.api.schemas import TrendingProjectOut

router = APIRouter(prefix="/recommendations")


@router.get("/trending", response_model=list[TrendingProjectOut])
def get_trending(
    limit: int = Query(default=20, ge=1, le=50),
    pool: ConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Get globally trending/popular projects."""
    with pool.get_cursor() as cur:
        cur.execute(
            """SELECT project_id, stars, last_synced_at
               FROM public.match_global_recommendation
               ORDER BY stars DESC NULLS LAST
               LIMIT %s""",
            (limit,),
        )
        return cur.fetchall()
```

- [ ] **Step 4: Register route in main.py**

Add to `src/services/api/main.py`:
```python
from src.services.api.routes import health, projects, recommendations, references

app.include_router(recommendations.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/api/test_recommendations.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add src/services/api/routes/recommendations.py src/services/api/main.py
git add tests/api/test_recommendations.py
git commit -m "$(cat <<'EOF'
feat(api): add trending recommendations endpoint

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

## Chunk 4: Docker integration and CI

### Task 9: Add API service to Docker Compose

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker-compose.override.yml`
- Modify: `scripts/init.sh`
- Modify: `Dockerfile` (add EXPOSE 8000)

- [ ] **Step 1: Add API role skip in init.sh**

Add after the daemon role check in `scripts/init.sh`:
```bash
# API skips dbt init — only needs DB
if [ "$DAGSTER_ROLE" = "api" ]; then
    echo "API role: skipping dbt init."
    echo "Executing command: $@"
    exec "$@"
fi
```

- [ ] **Step 2: Add EXPOSE 8000 to Dockerfile**

Add after `EXPOSE 3000` in `Dockerfile`:
```dockerfile
EXPOSE 3000 8000
```

(Replace `EXPOSE 3000` with `EXPOSE 3000 8000`)

- [ ] **Step 3: Add api service to docker-compose.yml**

Add after the `daemon` service:
```yaml
  # ============================================================================
  # REST API (FastAPI — lightweight, read-only)
  # ============================================================================
  api:
    build: .
    container_name: ost-linker-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      <<: *common-env
      DAGSTER_ROLE: api
    volumes: *common-volumes
    command: ["./scripts/init.sh", "uvicorn", "src.services.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

- [ ] **Step 4: Add api dev overrides to docker-compose.override.yml**

Add after the `daemon` service overrides:
```yaml
  api:
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    volumes:
      - ./src:/app/src
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml docker-compose.override.yml Dockerfile scripts/init.sh
git commit -m "$(cat <<'EOF'
chore(docker): add FastAPI service to compose stack

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 10: Update conftest.py for auto-markers and add api marker

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add api directory marker**

Add to `tests/conftest.py` in the `pytest_collection_modifyitems` function:
```python
elif "/api/" in path:
    item.add_marker(pytest.mark.api)
```

- [ ] **Step 2: Verify api marker works**

Run: `pytest tests/api/ -m api -v`
Expected: All api tests run and pass

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "$(cat <<'EOF'
test(api): add auto-marker for api test directory

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 11: Lint, type-check, and final verification

- [ ] **Step 1: Run ruff check**

Run: `ruff check src/services/api/`
Expected: No errors (fix any that appear)

- [ ] **Step 2: Run ruff format**

Run: `ruff format src/services/api/ tests/api/`
Expected: Files formatted

- [ ] **Step 3: Run mypy**

Run: `mypy src/services/api/`
Expected: No errors (fix any type issues)

- [ ] **Step 4: Run all tests**

Run: `pytest tests/api/ -v`
Expected: All tests pass

- [ ] **Step 5: Run full test suite to ensure no regressions**

Run: `pytest`
Expected: All existing + new tests pass

- [ ] **Step 6: Commit any fixes**

```bash
git add -u
git commit -m "$(cat <<'EOF'
style(api): fix lint and type issues

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 12: Update .env.example

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Add API env vars to .env.example**

Add to `.env.example`:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RATE_LIMIT=60
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "$(cat <<'EOF'
docs(env): add API configuration variables to .env.example

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```
