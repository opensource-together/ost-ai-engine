from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.services.api.config import APIConfig
from src.services.api.dependencies import close_pool, init_pool
from src.services.api.routes import health, projects, recommendations, references


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
app.include_router(references.router)
app.include_router(projects.router)
app.include_router(recommendations.router)
