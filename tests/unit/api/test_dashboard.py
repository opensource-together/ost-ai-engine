from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import ProgrammingError

from src.api.dashboard import load_dashboard, render_dashboard_html
from src.api.dependencies import get_db
from src.api.main import app
from src.api.schemas import DashboardOut, RankerMetricsOut


def _result(first: dict | None = None) -> MagicMock:
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = first
    return mock_result


def _session_from_rows(rows: list[dict | None]) -> MagicMock:
    session = MagicMock()
    session.execute.side_effect = [_result(row) for row in rows]
    return session


class TestLoadDashboard:
    def test_maps_core_feedback_and_ranker_rows(self) -> None:
        created = datetime(2026, 8, 31, tzinfo=UTC)
        session = _session_from_rows(
            [
                {
                    "user_count": 4,
                    "project_count": 12,
                    "bookmark_count": 3,
                    "personalized_pairs": 20,
                    "shown_events": 8,
                    "positive_events": 2,
                },
                {"feedback_impressions": 7, "feedback_positives": 1},
                {
                    "version": 3,
                    "sample_count": 120,
                    "positive_count": 15,
                    "negative_count": 105,
                    "precision_at_10": 0.4,
                    "recall_at_10": 0.5,
                    "ndcg_at_10": 0.6,
                    "baseline_ndcg_at_10": 0.55,
                    "created_at": created,
                },
            ]
        )

        snapshot = load_dashboard(session)

        assert snapshot.user_count == 4
        assert snapshot.feedback_positives == 1
        assert snapshot.ranker is not None
        assert snapshot.ranker.version == 3
        assert snapshot.ranker.ndcg_at_10 == 0.6

    def test_missing_optional_tables_yield_zeros(self) -> None:
        session = MagicMock()
        session.execute.side_effect = [
            _result(
                {
                    "user_count": 1,
                    "project_count": 2,
                    "bookmark_count": 0,
                    "personalized_pairs": 0,
                    "shown_events": 0,
                    "positive_events": 0,
                }
            ),
            ProgrammingError("feedback", {}, Exception("undefined table")),
            ProgrammingError("ranker", {}, Exception("undefined table")),
        ]

        snapshot = load_dashboard(session)

        assert snapshot.user_count == 1
        assert snapshot.feedback_impressions == 0
        assert snapshot.ranker is None
        assert session.rollback.call_count == 2


class TestRenderDashboardHtml:
    def test_includes_kpis_and_escapes_ranker_fallback(self) -> None:
        html = render_dashboard_html(
            DashboardOut(
                user_count=2,
                project_count=5,
                bookmark_count=1,
                shown_events=0,
                positive_events=0,
                personalized_pairs=9,
                feedback_impressions=0,
                feedback_positives=0,
                ranker=None,
            )
        )
        assert "Users" in html
        assert ">2<" in html
        assert "not trained" in html
        assert "<script>" not in html

    def test_includes_ranker_metrics_when_trained(self) -> None:
        html = render_dashboard_html(
            DashboardOut(
                user_count=0,
                project_count=0,
                bookmark_count=0,
                shown_events=0,
                positive_events=0,
                personalized_pairs=0,
                feedback_impressions=0,
                feedback_positives=0,
                ranker=RankerMetricsOut(
                    version=1,
                    sample_count=100,
                    positive_count=10,
                    negative_count=90,
                    precision_at_10=0.25,
                    recall_at_10=0.5,
                    ndcg_at_10=0.4,
                    baseline_ndcg_at_10=0.3,
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                ),
            )
        )
        assert "Precision@10" in html
        assert "0.250" in html


class TestDashboardRoutes:
    def test_json_endpoint_returns_snapshot(self, client: TestClient) -> None:
        session = _session_from_rows(
            [
                {
                    "user_count": 1,
                    "project_count": 1,
                    "bookmark_count": 0,
                    "personalized_pairs": 0,
                    "shown_events": 0,
                    "positive_events": 0,
                },
                {"feedback_impressions": 0, "feedback_positives": 0},
                None,
            ]
        )
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get("/v1/dashboard")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        body = response.json()
        assert body["user_count"] == 1
        assert body["ranker"] is None

    def test_ui_endpoint_returns_html(self, client: TestClient) -> None:
        session = _session_from_rows(
            [
                {
                    "user_count": 0,
                    "project_count": 0,
                    "bookmark_count": 0,
                    "personalized_pairs": 0,
                    "shown_events": 0,
                    "positive_events": 0,
                },
                None,
                None,
            ]
        )
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get("/v1/dashboard/ui")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "Recommendation quality" in response.text
