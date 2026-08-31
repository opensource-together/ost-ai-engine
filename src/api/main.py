import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.api.auth import require_service_token
from src.api.config import APIConfig
from src.api.dependencies import close_db, init_db, init_semantic
from src.api.errors import register_error_handlers
from src.api.middleware import SecurityHeadersMiddleware
from src.api.rate_limit import limiter
from src.api.routes.v1 import dashboard, health, projects, recommendations, references
from src.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


def _get_config() -> APIConfig:
    return APIConfig()  # type: ignore[call-arg]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init DB; optionally load semantic model. Shutdown: dispose DB."""
    configure_logging()
    config = _get_config()
    token_ok = config.service_token and config.service_token.strip()
    if config.require_service_token and not token_ok:
        msg = (
            "OST_LINKER_REQUIRE_SERVICE_TOKEN is enabled but "
            "OST_LINKER_SERVICE_TOKEN is missing or empty — set a shared secret or "
            "turn off strict mode for local dev."
        )
        raise RuntimeError(msg)
    logger.info("Initializing API database connection")
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
    logger.info("API shutdown complete")


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Rate limit exceeded",
            }
        },
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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)  # type: ignore[arg-type]
register_error_handlers(app)
app.add_middleware(SecurityHeadersMiddleware)

protected = [Depends(require_service_token)]

v1 = APIRouter(prefix="/v1")
v1.include_router(
    references.router,
    prefix="/references",
    dependencies=protected,
    tags=["references"],
)
v1.include_router(projects.router, dependencies=protected, tags=["projects"])
v1.include_router(
    recommendations.router,
    dependencies=protected,
    tags=["recommendations"],
)
v1.include_router(
    dashboard.router,
    dependencies=protected,
    tags=["dashboard"],
)

app.include_router(health.router, tags=["health"])
app.include_router(v1)
