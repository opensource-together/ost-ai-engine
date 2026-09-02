"""Prometheus HTTP metrics for the Linker API."""

from collections.abc import Iterator
from time import perf_counter
from typing import Any

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from prometheus_client.core import CounterMetricFamily
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REGISTRY = CollectorRegistry()

_USAGE_SQL = """
SELECT
  COALESCE(SUM("promptTokens"), 0) AS prompt_tokens,
  COALESCE(SUM("completionTokens"), 0) AS completion_tokens,
  COALESCE(SUM("estimatedCostUsd"), 0) AS estimated_cost_usd,
  COALESCE(SUM(requests), 0) AS requests,
  COALESCE(SUM("http402"), 0) AS http_402,
  COALESCE(SUM("http429"), 0) AS http_429
FROM match.llm_usage
"""

_ZERO_USAGE: dict[str, float] = {
    "prompt_tokens": 0.0,
    "completion_tokens": 0.0,
    "estimated_cost_usd": 0.0,
    "requests": 0.0,
    "http_402": 0.0,
    "http_429": 0.0,
}


def _usage_totals() -> dict[str, float]:
    """Lifetime classifier usage from Postgres; zeros if DB is unavailable."""
    from src.api.dependencies import _session_factory

    if _session_factory is None:
        return dict(_ZERO_USAGE)
    db = _session_factory()
    try:
        row = db.execute(text(_USAGE_SQL)).mappings().first()
    except Exception:
        return dict(_ZERO_USAGE)
    finally:
        db.close()
    if not row:
        return dict(_ZERO_USAGE)
    out = dict(_ZERO_USAGE)
    for key in out:
        try:
            out[key] = float(row[key] or 0)
        except (KeyError, TypeError, ValueError):
            continue
    return out


class MistralUsageCollector:
    """Expose match.llm_usage sums so Grafana can chart Mistral spend."""

    def collect(self) -> Iterator[Any]:
        stats = _usage_totals()
        prompt = CounterMetricFamily(
            "linker_mistral_prompt_tokens_total",
            "Prompt tokens sent to Mistral by the project classifier.",
        )
        prompt.add_metric([], stats["prompt_tokens"])
        yield prompt

        completion = CounterMetricFamily(
            "linker_mistral_completion_tokens_total",
            "Completion tokens returned by Mistral for classification.",
        )
        completion.add_metric([], stats["completion_tokens"])
        yield completion

        cost = CounterMetricFamily(
            "linker_mistral_estimated_cost_usd_total",
            "Estimated Mistral classification cost in USD (list price, not invoice).",
        )
        cost.add_metric([], stats["estimated_cost_usd"])
        yield cost

        requests = CounterMetricFamily(
            "linker_mistral_requests_total",
            "Mistral chat completion calls attempted by the classifier.",
        )
        requests.add_metric([], stats["requests"])
        yield requests

        http = CounterMetricFamily(
            "linker_mistral_http_responses_total",
            "Classifier Mistral HTTP outcomes by status code.",
            labels=["code"],
        )
        http.add_metric(["402"], stats["http_402"])
        http.add_metric(["429"], stats["http_429"])
        yield http


REGISTRY.register(MistralUsageCollector())

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
