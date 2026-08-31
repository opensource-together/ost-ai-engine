"""Live DB checks for the recommendation dashboard."""


class TestDashboardLive:
    def test_json_returns_counts(self, client_db) -> None:
        resp = client_db.get("/v1/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_count"] >= 0
        assert body["project_count"] >= 0
        assert "ranker" in body

    def test_ui_returns_html(self, client_db) -> None:
        resp = client_db.get("/v1/dashboard/ui")
        assert resp.status_code == 200
        assert "Recommendation quality" in resp.text
