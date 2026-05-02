import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.services.api.auth import require_service_token
from src.services.api.config import APIConfig
from src.services.api.dependencies import close_db, init_db, init_semantic
from src.services.api.rate_limit import limiter
from src.services.api.routes import health, projects, recommendations, references


def _get_config() -> APIConfig:
    return APIConfig()  # type: ignore[call-arg]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init DB; optionally load semantic model. Shutdown: dispose DB."""
    config = _get_config()
    token_ok = config.service_token and config.service_token.strip()
    if config.require_service_token and not token_ok:
        msg = (
            "OST_LINKER_REQUIRE_SERVICE_TOKEN is enabled but "
            "OST_LINKER_SERVICE_TOKEN is missing or empty — set a shared secret or "
            "turn off strict mode for local dev."
        )
        raise RuntimeError(msg)
    init_db(config.database_url)
    skip_semantic = os.environ.get("LINKER_SKIP_SEMANTIC_INIT", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if not skip_semantic:
        init_semantic()

    yield
    close_db()


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )


def _openapi_urls() -> tuple[str | None, str | None, str | None]:
    """Hide OpenAPI and UIs when API_ENABLE_OPENAPI is false (e.g. production)."""
    enabled = os.environ.get("API_ENABLE_OPENAPI", "true").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if enabled:
        return "/openapi.json", "/docs", "/redoc"
    return None, None, None


_openapi_json, _docs_url, _redoc_url = _openapi_urls()

app = FastAPI(
    title="OST Linker API",
    description="Open-source project recommendations",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url=_openapi_json,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# Rate limiting via @limiter.limit() decorators on routes.
# slowapi's SlowAPIMiddleware has compatibility issues with sync endpoints,
# so we use the per-route decorator approach instead.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)  # type: ignore[arg-type]

# NOTE: No CORS middleware — this API is consumed server-to-server by the MCP
# backend, not by browsers. Add CORSMiddleware if browser access is needed later.

app.include_router(health.router)
app.include_router(
    references.router,
    dependencies=[Depends(require_service_token)],
)
app.include_router(
    projects.router,
    dependencies=[Depends(require_service_token)],
)
app.include_router(
    recommendations.router,
    dependencies=[Depends(require_service_token)],
)
