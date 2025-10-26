"""Compatibility shim: re-export prisma_client from the services package.

Old code lived here; we now keep a small shim so existing imports
`from src.dagster.common import prisma_client` keep working.
"""

from src.services.python.prisma_client import prisma_client

__all__ = ["prisma_client"]
