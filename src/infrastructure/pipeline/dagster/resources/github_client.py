"""
Dagster resource providing an authenticated GitHub client using PyGithub.

This resource reads the access token from `src.infrastructure.config.settings`.
It is intended to be shared by ops that need to interact with the GitHub API.
"""

from __future__ import annotations

from typing import Any

from dagster import resource
from github import Github

from src.infrastructure.config import settings


@resource
def github_client(context) -> Github:
    """Create and return an authenticated PyGithub client.

    The token is read from application settings. If no token is configured,
    the client will operate in unauthenticated mode which is heavily rate-limited.

    Args:
        context: Dagster resource initialization context (unused).

    Returns:
        An instance of ``github.Github``.
    """
    # Prefer settings; allows central configuration via environment variables.
    token: str | None = getattr(settings, "GITHUB_ACCESS_TOKEN", None)
    if token and token != "your_github_token_here":
        return Github(login_or_token=token)

    # Fallback to unauthenticated client if token isn't provided (limited rate).
    context.log.warning(
        "GITHUB_ACCESS_TOKEN not set; using unauthenticated GitHub client (rate limits will be very low)."
    )
    return Github()


