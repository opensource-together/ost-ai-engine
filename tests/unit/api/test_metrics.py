from fastapi.testclient import TestClient


class TestMetrics:
    def test_metrics_is_prometheus_text(self, client: TestClient) -> None:
        client.get("/health")
        response = client.get("/metrics")
        assert response.status_code == 200
        body = response.text
        assert "linker_http_requests_total" in body
        assert 'path="/health"' in body
        assert 'path="/metrics"' not in body

    def test_metrics_stays_open_when_token_is_set(
        self, client: TestClient, monkeypatch
    ) -> None:
        monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", "expected-token")
        response = client.get("/metrics")
        assert response.status_code == 200
