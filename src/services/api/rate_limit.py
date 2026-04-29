import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def rate_limit_per_minute() -> str:
    """SlowAPI limit string; aligned with APIConfig.rate_limit / API_RATE_LIMIT."""
    raw = os.environ.get("API_RATE_LIMIT", "").strip()
    try:
        n = int(raw) if raw else 60
    except ValueError:
        n = 60
    if n < 1:
        n = 60
    return f"{n}/minute"


# Evaluated at import (workers inherit process env loaded before app code runs).
RATE_LIMIT = rate_limit_per_minute()

limiter = Limiter(key_func=get_remote_address)
