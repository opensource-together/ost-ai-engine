from unittest.mock import MagicMock

from fastapi.testclient import TestClient


class TestMetrics:
    def test_metrics_is_prometheus_text(self, client: TestClient) -> None:
        client.get("/health")
        response = client.get("/metrics")
        assert response.status_code == 200
        body = response.text
        assert "linker_http_requests_total" in body
        assert "linker_mistral_prompt_tokens_total" in body
        assert "linker_mistral_estimated_cost_usd_total" in body
        assert 'path="/health"' in body
        assert 'path="/metrics"' not in body

    def test_metrics_stays_open_when_token_is_set(
        self, client: TestClient, monkeypatch
    ) -> None:
        monkeypatch.setenv("OST_LINKER_SERVICE_TOKEN", "expected-token")
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_usage_totals_map_db_row(self, monkeypatch) -> None:
        session = MagicMock()
        session.execute.return_value.mappings.return_value.first.return_value = {
            "prompt_tokens": 4828,
            "completion_tokens": 43,
            "estimated_cost_usd": 0.001,
            "requests": 3,
            "http_402": 0,
            "http_429": 0,
        }
        monkeypatch.setattr("src.api.dependencies._session_factory", lambda: session)
        from src.api.metrics import _usage_totals

        stats = _usage_totals()
        assert stats["prompt_tokens"] == 4828.0
        assert stats["estimated_cost_usd"] == 0.001
