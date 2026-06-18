import os
import secrets

from fastapi import Header, HTTPException


def _expected_token() -> str | None:
    token = os.environ.get("OST_LINKER_SERVICE_TOKEN")
    if token and token.strip():
        return token.strip()
    return None


def require_service_token(
    x_service_token: str | None = Header(default=None),
) -> None:
    """Require X-Service-Token when a shared secret is configured."""
    expected = _expected_token()
    if expected is None:
        return

    if not secrets.compare_digest(x_service_token or "", expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing service token",
        )
