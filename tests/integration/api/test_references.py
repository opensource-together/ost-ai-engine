"""Live taxonomy endpoints after prisma seed."""

import pytest


class TestReferencesTaxonomyLive:
    @pytest.mark.parametrize(
        "path",
        [
            "/v1/references/categories",
            "/v1/references/domains",
            "/v1/references/techstacks",
        ],
    )
    def test_list_nonempty(self, client_db, path: str) -> None:
        r = client_db.get(path)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1, f"{path} expected seed data"
