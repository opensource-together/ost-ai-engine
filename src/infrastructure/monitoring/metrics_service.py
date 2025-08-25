"""
Metrics service for monitoring and observability.

Provides centralized metrics collection, aggregation, and reporting
for the data engine system.
"""

import json
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.infrastructure.logger import log


@dataclass
class MetricPoint:
    """Represents a single metric data point."""

    timestamp: datetime
    value: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Represents a metric with multiple data points."""

    name: str
    description: str
    unit: str
    data_points: deque = field(default_factory=lambda: deque(maxlen=1000))
    tags: dict[str, str] = field(default_factory=dict)


class MetricsService:
    """
    Centralized metrics collection and reporting service.

    Features:
    - Real-time metrics collection
    - Aggregation and statistics
    - Performance monitoring
    - Alerting capabilities
    - Export to monitoring systems
    """

    def __init__(self):
        self._metrics: dict[str, Metric] = {}
        self._lock = threading.Lock()
        self._start_time = datetime.now()

        # Initialize default metrics
        self._init_default_metrics()

    def _init_default_metrics(self):
        """Initialize default system metrics."""
        self.register_metric("api_requests_total", "Total API requests", "count")
        self.register_metric("api_response_time", "API response time", "ms")
        self.register_metric("db_queries_total", "Total database queries", "count")
        self.register_metric("db_query_time", "Database query time", "ms")
        self.register_metric("cache_hits", "Cache hit rate", "percentage")
        self.register_metric("model_operations", "ML model operations", "count")
        self.register_metric("errors_total", "Total errors", "count")
        self.register_metric("memory_usage", "Memory usage", "MB")
        self.register_metric("cpu_usage", "CPU usage", "percentage")

    def register_metric(
        self, name: str, description: str, unit: str, tags: dict[str, str] = None
    ):
        """Register a new metric."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Metric(
                    name=name, description=description, unit=unit, tags=tags or {}
                )
                log.info(f"Registered metric: {name} ({description})")

    def record_metric(self, name: str, value: float, tags: dict[str, str] = None):
        """Record a metric value."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                metric.data_points.append(
                    MetricPoint(timestamp=datetime.now(), value=value, tags=tags or {})
                )

                # Log performance metric
                from src.infrastructure.logger import log_performance_metric

                log_performance_metric(name, value, metric.unit, tags)

    def get_metric_stats(self, name: str, window_minutes: int = 60) -> dict[str, Any]:
        """Get statistics for a metric over a time window."""
        with self._lock:
            if name not in self._metrics:
                return {}

            metric = self._metrics[name]
            cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

            # Filter data points within window
            recent_points = [
                point for point in metric.data_points if point.timestamp >= cutoff_time
            ]

            if not recent_points:
                return {
                    "name": name,
                    "description": metric.description,
                    "unit": metric.unit,
                    "count": 0,
                    "min": None,
                    "max": None,
                    "avg": None,
                    "latest": None,
                }

            values = [point.value for point in recent_points]

            return {
                "name": name,
                "description": metric.description,
                "unit": metric.unit,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": values[-1] if values else None,
                "window_minutes": window_minutes,
            }

    def get_all_metrics_stats(
        self, window_minutes: int = 60
    ) -> dict[str, dict[str, Any]]:
        """Get statistics for all metrics."""
        with self._lock:
            return {
                name: self.get_metric_stats(name, window_minutes)
                for name in self._metrics
            }

    def record_api_request(
        self, method: str, path: str, status_code: int, response_time: float
    ):
        """Record API request metrics."""
        # Increment total requests
        self.record_metric(
            "api_requests_total",
            1,
            {"method": method, "path": path, "status_code": str(status_code)},
        )

        # Record response time
        self.record_metric(
            "api_response_time",
            response_time,
            {"method": method, "path": path, "status_code": str(status_code)},
        )

        # Log API request
        from src.infrastructure.logger import log_api_request

        log_api_request(method, path, status_code, response_time)

    def record_database_query(
        self, query_type: str, table: str, duration: float, rows_affected: int = None
    ):
        """Record database query metrics."""
        # Increment total queries
        self.record_metric(
            "db_queries_total", 1, {"query_type": query_type, "table": table}
        )

        # Record query time
        self.record_metric(
            "db_query_time", duration, {"query_type": query_type, "table": table}
        )

        # Log database query
        from src.infrastructure.logger import log_database_query

        log_database_query(query_type, table, duration, rows_affected)

    def record_cache_operation(
        self, operation: str, key: str, hit: bool, duration: float = None
    ):
        """Record cache operation metrics."""
        # Record cache hit/miss
        hit_value = 1 if hit else 0
        self.record_metric(
            "cache_hits", hit_value, {"operation": operation, "key": key}
        )

        # Log cache operation
        from src.infrastructure.logger import log_cache_operation

        log_cache_operation(operation, key, hit, duration)

    def record_model_operation(
        self, operation: str, model_name: str, duration: float, success: bool
    ):
        """Record ML model operation metrics."""
        # Increment model operations
        self.record_metric(
            "model_operations",
            1,
            {"operation": operation, "model": model_name, "success": str(success)},
        )

        # Log model operation
        from src.infrastructure.logger import log_model_operation

        log_model_operation(operation, model_name, duration, success)

    def record_error(self, error_type: str, context: str = None):
        """Record error metrics."""
        # Increment error count
        self.record_metric(
            "errors_total",
            1,
            {"error_type": error_type, "context": context or "unknown"},
        )

        log.error(f"Error recorded: {error_type} - Context: {context}")

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health metrics."""
        uptime = datetime.now() - self._start_time

        # Get recent metrics
        recent_stats = self.get_all_metrics_stats(window_minutes=5)

        # Calculate health indicators
        error_rate = 0
        if "errors_total" in recent_stats and "api_requests_total" in recent_stats:
            error_count = recent_stats["errors_total"]["count"]
            request_count = recent_stats["api_requests_total"]["count"]
            if request_count > 0:
                error_rate = (error_count / request_count) * 100

        avg_response_time = 0
        if "api_response_time" in recent_stats:
            avg_response_time = recent_stats["api_response_time"]["avg"] or 0

        cache_hit_rate = 0
        if "cache_hits" in recent_stats:
            cache_stats = recent_stats["cache_hits"]
            if cache_stats["count"] > 0:
                cache_hit_rate = (cache_stats["avg"] or 0) * 100

        return {
            "status": (
                "healthy" if error_rate < 5 and avg_response_time < 1000 else "degraded"
            ),
            "uptime_seconds": uptime.total_seconds(),
            "error_rate_percent": error_rate,
            "avg_response_time_ms": avg_response_time,
            "cache_hit_rate_percent": cache_hit_rate,
            "metrics_count": len(self._metrics),
            "last_updated": datetime.now().isoformat(),
        }

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        with self._lock:
            if format == "json":
                return json.dumps(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "system_health": self.get_system_health(),
                        "metrics": self.get_all_metrics_stats(),
                    },
                    indent=2,
                    default=str,
                )
            else:
                raise ValueError(f"Unsupported format: {format}")


# Global metrics service instance
metrics_service = MetricsService()
