"""
FastAPI middleware for automatic monitoring and metrics collection.
"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.monitoring.metrics_service import metrics_service


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic monitoring of FastAPI requests.

    Features:
    - Request/response timing
    - Status code tracking
    - Error monitoring
    - Performance metrics
    - Automatic logging
    """

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip monitoring for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Record metrics
            metrics_service.record_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=response_time,
            )

            # Add response time header
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"

            return response

        except Exception as e:
            # Calculate response time even for errors
            response_time = (time.time() - start_time) * 1000

            # Record error metrics
            metrics_service.record_error(
                error_type=type(e).__name__,
                context=f"API Request: {request.method} {request.url.path}",
            )

            # Log error
            from src.infrastructure.logger import log_error

            log_error(e, f"API Request: {request.method} {request.url.path}")

            # Re-raise the exception
            raise


class DatabaseMonitoringMiddleware:
    """
    Middleware for monitoring database operations.
    """

    @staticmethod
    def monitor_query(
        query_type: str, table: str, duration: float, rows_affected: int = None
    ):
        """Monitor a database query."""
        metrics_service.record_database_query(
            query_type, table, duration, rows_affected
        )

    @staticmethod
    def monitor_connection_pool(stats: dict):
        """Monitor database connection pool statistics."""
        if "pool_size" in stats:
            metrics_service.record_metric("db_pool_size", stats["pool_size"])
        if "checked_out" in stats:
            metrics_service.record_metric("db_connections_active", stats["checked_out"])
        if "checked_in" in stats:
            metrics_service.record_metric("db_connections_idle", stats["checked_in"])


class CacheMonitoringMiddleware:
    """
    Middleware for monitoring cache operations.
    """

    @staticmethod
    def monitor_cache_operation(
        operation: str, key: str, hit: bool, duration: float = None
    ):
        """Monitor a cache operation."""
        metrics_service.record_cache_operation(operation, key, hit, duration)

    @staticmethod
    def monitor_cache_stats(stats: dict):
        """Monitor cache statistics."""
        if "hits" in stats and "misses" in stats:
            total_requests = stats["hits"] + stats["misses"]
            if total_requests > 0:
                hit_rate = (stats["hits"] / total_requests) * 100
                metrics_service.record_metric("cache_hit_rate", hit_rate)


class ModelMonitoringMiddleware:
    """
    Middleware for monitoring ML model operations.
    """

    @staticmethod
    def monitor_model_operation(
        operation: str, model_name: str, duration: float, success: bool
    ):
        """Monitor a model operation."""
        metrics_service.record_model_operation(operation, model_name, duration, success)

    @staticmethod
    def monitor_model_performance(
        model_name: str, prediction_time: float, accuracy: float = None
    ):
        """Monitor model performance metrics."""
        metrics_service.record_metric(
            "model_prediction_time", prediction_time, {"model": model_name}
        )

        if accuracy is not None:
            metrics_service.record_metric(
                "model_accuracy", accuracy, {"model": model_name}
            )


# Decorator for monitoring function performance
def monitor_performance(metric_name: str, tags: dict = None):
    """
    Decorator to monitor function performance.

    Args:
        metric_name: Name of the metric to record
        tags: Additional tags for the metric
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                metrics_service.record_metric(metric_name, duration, tags)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                metrics_service.record_metric(metric_name, duration, tags)
                metrics_service.record_error(
                    error_type=type(e).__name__, context=f"Function: {func.__name__}"
                )
                raise

        return wrapper

    return decorator
