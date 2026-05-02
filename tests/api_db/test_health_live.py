"""Live DB checks for FastAPI `/health`."""


class TestHealthLive:
    def test_health_returns_ok_with_real_db(self, client_db) -> None:
        resp = client_db.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
