import os

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply markers based on path; skip live DB suite when DATABASE_URL unset."""
    skip_live = pytest.mark.skip(
        reason=(
            "Database-tier tests skipped: export DATABASE_URL to a reachable Postgres "
            "(see ost-linker AGENTS.md verification tiers)."
        ),
    )

    for item in items:
        path = str(item.fspath)

        if "/api_db/" in path:
            item.add_marker(pytest.mark.database)

        if "/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/api/" in path and "/api_db/" not in path:
            item.add_marker(pytest.mark.api)

        if "/api_db/" in path and not os.environ.get("DATABASE_URL"):
            item.add_marker(skip_live)
