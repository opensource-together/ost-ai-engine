import os
from contextlib import contextmanager


@contextmanager
def prisma_client():
    """Context manager to initialize Prisma client with cache envs."""
    os.environ.setdefault("PRISMA_BINARY_CACHE_DIR", "")
    os.environ.setdefault("XDG_CACHE_HOME", "")
    from prisma import Prisma
    prisma = Prisma()
    prisma.connect()
    try:
        yield prisma
    finally:
        try:
            prisma.disconnect()
        except Exception:
            pass
