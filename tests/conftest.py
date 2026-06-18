import os

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply markers by test path; skip live DB and AI suites when unset."""
    skip_live = pytest.mark.skip(
        reason=(
            "Database-tier tests skipped: export DATABASE_URL to a reachable Postgres "
            "(see ost-linker AGENTS.md verification tiers)."
        ),
    )
    skip_ai = pytest.mark.skip(
        reason="AI tests skipped: set RUN_AI_TESTS=1 to enable real LLM/API calls.",
    )

    for item in items:
        path = str(item.fspath)

        if "/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in path:
            item.add_marker(pytest.mark.integration)

        if "/integration/api/" in path:
            item.add_marker(pytest.mark.database)

        if "/ai/" in path:
            item.add_marker(pytest.mark.ai)
            if not os.environ.get("RUN_AI_TESTS"):
                item.add_marker(skip_ai)

        if "/integration/api/" in path and not os.environ.get("DATABASE_URL"):
            item.add_marker(skip_live)
