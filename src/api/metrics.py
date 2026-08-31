"""Prometheus HTTP metrics for the Linker API."""

from time import perf_counter

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REGISTRY = CollectorRegistry()

REQUESTS = Counter(
    "linker_http_requests_total",
    "HTTP requests handled by the Linker API",
    ["method", "path", "status"],
    registry=REGISTRY,
)
DURATION = Histogram(
    "linker_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    registry=REGISTRY,
)

_SKIP_PATHS = frozenset({"/metrics"})


def metrics_body() -> bytes:
    return generate_latest(REGISTRY)


def _route_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return request.url.path


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record request count and latency; skip the scrape endpoint itself."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)
        started = perf_counter()
        response = await call_next(request)
        path = _route_path(request)
        REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        DURATION.labels(request.method, path).observe(perf_counter() - started)
        return response
