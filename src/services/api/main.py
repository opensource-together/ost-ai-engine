from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.services.api.config import APIConfig
from src.services.api.dependencies import close_pool, init_pool
from src.services.api.rate_limit import limiter
from src.services.api.routes import health, projects, recommendations, references


def _get_config() -> APIConfig:
    return APIConfig()  # type: ignore[call-arg]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init pool. Shutdown: close pool."""
    config = _get_config()
    init_pool(config.database_url)
    yield
    close_pool()


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
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

# Rate limiting via @limiter.limit() decorators on routes.
# slowapi's SlowAPIMiddleware has compatibility issues with sync endpoints,
# so we use the per-route decorator approach instead.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)  # type: ignore[arg-type]

# NOTE: No CORS middleware — this API is consumed server-to-server by the MCP
# backend, not by browsers. Add CORSMiddleware if browser access is needed later.

app.include_router(health.router)
app.include_router(references.router)
app.include_router(projects.router)
app.include_router(recommendations.router)
