"""Live DB checks for GET /v1/recommendations/for-you."""

from uuid import uuid4


class TestForYouLive:
    def test_missing_user_id_is_422(self, client_db) -> None:
        resp = client_db.get("/v1/recommendations/for-you")
        assert resp.status_code == 422

    def test_unknown_user_is_404(self, client_db) -> None:
        resp = client_db.get(f"/v1/recommendations/for-you?user_id={uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
