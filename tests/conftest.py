import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply markers based on test directory."""
    for item in items:
        path = str(item.fspath)
        if "/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/api/" in path:
            item.add_marker(pytest.mark.api)
