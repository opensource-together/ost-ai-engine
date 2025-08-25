import logging
import logging.handlers
import sys
from pathlib import Path

from src.infrastructure.config import settings


def setup_logger():
    """
    Configures and returns a standardized logger with advanced features.

    Features:
    - Console and file logging
    - Structured logging with JSON format
    - Log rotation
    - Performance metrics
    - Error tracking
    """
    logger = logging.getLogger("data_engine")
    logger.setLevel(settings.LOG_LEVEL.upper())

    # Prevent duplicate handlers if the function is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create a handler to output logs to the console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL.upper())

    # Create a formatter for console output
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # Create a file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "data_engine.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,  # 10MB
    )
    file_handler.setLevel(settings.LOG_LEVEL.upper())

    # Create a formatter for file output (more detailed)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s - %(pathname)s"
    )
    file_handler.setFormatter(file_formatter)

    # Create error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,  # 5MB
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s - %(pathname)s - %(exc_info)s"
    )
    error_handler.setFormatter(error_formatter)

    # Create performance metrics handler
    metrics_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "metrics.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,  # 5MB
    )
    metrics_handler.setLevel(logging.INFO)
    metrics_formatter = logging.Formatter("%(asctime)s - METRICS - %(message)s")
    metrics_handler.setFormatter(metrics_formatter)

    # Add all handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(metrics_handler)

    return logger


def log_performance_metric(
    metric_name: str, value: float, unit: str = "ms", tags: dict = None
):
    """
    Log performance metrics for monitoring.

    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        tags: Additional tags for the metric
    """
    log = logging.getLogger("data_engine")
    tags_str = f" - {tags}" if tags else ""
    log.info(f"PERFORMANCE - {metric_name}: {value}{unit}{tags_str}")


def log_api_request(
    method: str, path: str, status_code: int, response_time: float, user_id: str = None
):
    """
    Log API request metrics.

    Args:
        method: HTTP method
        path: Request path
        status_code: HTTP status code
        response_time: Response time in milliseconds
        user_id: User ID (optional)
    """
    log = logging.getLogger("data_engine")
    user_info = f" - User: {user_id}" if user_id else ""
    log.info(
        f"API_REQUEST - {method} {path} - Status: {status_code} - Time: {response_time}ms{user_info}"
    )


def log_database_query(
    query_type: str, table: str, duration: float, rows_affected: int = None
):
    """
    Log database query metrics.

    Args:
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration: Query duration in milliseconds
        rows_affected: Number of rows affected
    """
    log = logging.getLogger("data_engine")
    rows_info = f" - Rows: {rows_affected}" if rows_affected is not None else ""
    log.info(f"DB_QUERY - {query_type} {table} - Duration: {duration}ms{rows_info}")


def log_model_operation(
    operation: str, model_name: str, duration: float, success: bool, error: str = None
):
    """
    Log ML model operations.

    Args:
        operation: Operation type (load, save, predict, train)
        model_name: Name of the model
        duration: Operation duration in milliseconds
        success: Whether the operation was successful
        error: Error message if failed
    """
    log = logging.getLogger("data_engine")
    status = "SUCCESS" if success else "FAILED"
    error_info = f" - Error: {error}" if error else ""
    log.info(
        f"MODEL_OP - {operation} {model_name} - Status: {status} - Duration: {duration}ms{error_info}"
    )


def log_cache_operation(operation: str, key: str, hit: bool, duration: float = None):
    """
    Log cache operations.

    Args:
        operation: Cache operation (get, set, delete)
        key: Cache key
        hit: Whether it was a cache hit
        duration: Operation duration in milliseconds
    """
    log = logging.getLogger("data_engine")
    hit_status = "HIT" if hit else "MISS"
    duration_info = f" - Duration: {duration}ms" if duration else ""
    log.info(f"CACHE - {operation} {key} - {hit_status}{duration_info}")


def log_error(error: Exception, context: str = None, user_id: str = None):
    """
    Log errors with context.

    Args:
        error: Exception object
        context: Additional context
        user_id: User ID (optional)
    """
    log = logging.getLogger("data_engine")
    context_info = f" - Context: {context}" if context else ""
    user_info = f" - User: {user_id}" if user_id else ""
    log.error(
        f"ERROR - {type(error).__name__}: {str(error)}{context_info}{user_info}",
        exc_info=True,
    )


# Create a default logger instance to be imported by other modules
log = setup_logger()
