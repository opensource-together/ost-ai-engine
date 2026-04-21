import os
import secrets

from fastapi import Header, HTTPException


def require_service_token(
    x_service_token: str | None = Header(default=None),
) -> None:
    """Require X-Service-Token when service-token auth is enabled."""
    expected = os.environ.get("OST_LINKER_SERVICE_TOKEN")
    if not expected:
        return

    if not secrets.compare_digest(x_service_token or "", expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing service token",
        )
