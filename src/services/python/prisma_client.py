import os
import logging
from contextlib import contextmanager


@contextmanager
def prisma_client():
    """Context manager to initialize Prisma client with defensive logging.

    This function is intentionally defensive: importing the Prisma package or
    connecting the query engine can fail (or the engine binary may be
    incompatible). In those cases we log the error and yield ``None`` so
    callers can decide to skip DB writes instead of letting the child
    process crash with an uncontrolled signal.
    """
    # Keep caches unset to avoid unexpected cache dirs in containerized runs
    os.environ.setdefault("PRISMA_BINARY_CACHE_DIR", "")
    os.environ.setdefault("XDG_CACHE_HOME", "")

    try:
        from prisma import Prisma
    except Exception as e:
        logging.exception("prisma_client: failed to import prisma package: %s", e)
        # Yield None so callers can skip DB work gracefully
        yield None
        return

    prisma = None
    try:
        prisma = Prisma()
    except Exception as e:
        logging.exception("prisma_client: failed to instantiate Prisma(): %s", e)
        yield None
        return

    try:
        # Attempt to connect; this can raise if the query-engine binary is
        # missing/incompatible. Catch and log so the worker doesn't fail
        # without a clear diagnostic in logs.
        prisma.connect()
    except Exception as e:
        logging.exception("prisma_client: prisma.connect() failed: %s", e)
        # Try to cleanup if the client partially initialized
        try:
            prisma.disconnect()
        except Exception:
            pass
        yield None
        return

    try:
        yield prisma
    finally:
        try:
            prisma.disconnect()
        except Exception:
            pass
