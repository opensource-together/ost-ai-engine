from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_db
from src.api.main import app

USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def _recommendation(
    project_id: str, final_score: float, embedding: object
) -> dict[str, object]:
    return {
        "project_id": project_id,
        "title": project_id.title(),
        "description": f"{project_id} description",
        "repo_url": f"https://github.com/ost/{project_id}",
        "similarity_score": 0.8,
        "preference_score": 0.5,
        "freshness_score": 0.4,
        "popularity_score": 0.2,
        "final_score": final_score,
        "embedding": embedding,
    }


def _session_user_then_rows(user: dict | None, rows: list[dict]) -> MagicMock:
    user_result = MagicMock()
    user_result.mappings.return_value.first.return_value = user
    reco_result = MagicMock()
    reco_result.mappings.return_value.all.return_value = rows
    session = MagicMock()
    session.execute.side_effect = [user_result, reco_result]
    return session


class TestForYou:
    def test_requires_user_id(self, client: TestClient) -> None:
        response = client.get("/v1/recommendations/for-you")
        assert response.status_code == 422

    def test_rejects_invalid_user_id(self, client: TestClient) -> None:
        response = client.get("/v1/recommendations/for-you?user_id=not-a-uuid")
        assert response.status_code == 422

    def test_unknown_user_returns_404(self, client: TestClient) -> None:
        session = _session_user_then_rows(None, [])
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get(f"/v1/recommendations/for-you?user_id={USER_ID}")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"

    def test_returns_ranked_recommendations(self, client: TestClient) -> None:
        rows = [
            {
                "project_id": "proj-1",
                "title": "Linker",
                "description": "Reco engine",
                "repo_url": "https://github.com/ost/linker",
                "similarity_score": 0.8,
                "preference_score": 0.5,
                "freshness_score": 0.4,
                "popularity_score": 0.2,
                "final_score": 0.62,
            }
        ]
        session = _session_user_then_rows({"id": str(USER_ID)}, rows)
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get(f"/v1/recommendations/for-you?user_id={USER_ID}")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["project_id"] == "proj-1"
        assert data[0]["title"] == "Linker"
        assert data[0]["final_score"] == 0.62

    def test_empty_list_when_user_has_no_recos(self, client: TestClient) -> None:
        session = _session_user_then_rows({"id": str(USER_ID)}, [])
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get(f"/v1/recommendations/for-you?user_id={USER_ID}")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        assert response.json() == []

    def test_respects_limit(self, client: TestClient) -> None:
        session = _session_user_then_rows({"id": str(USER_ID)}, [])
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get(
                f"/v1/recommendations/for-you?user_id={USER_ID}&limit=5"
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        sql = str(session.execute.call_args_list[1].args[0])
        assert "LIMIT" in sql.upper()
        assert session.execute.call_args_list[1].args[1]["limit"] == 15

    def test_diversifies_recommendation_order(self, client: TestClient) -> None:
        rows = [
            _recommendation("first", 1.0, "[1.0, 0.0]"),
            _recommendation("similar", 0.9, "[1.0, 0.0]"),
            _recommendation("diverse", 0.8, "[0.0, 1.0]"),
        ]
        session = _session_user_then_rows({"id": str(USER_ID)}, rows)
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get(
                f"/v1/recommendations/for-you?user_id={USER_ID}&limit=2"
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        assert [item["project_id"] for item in response.json()] == [
            "first",
            "diverse",
        ]

    @pytest.mark.parametrize(
        ("invalid_embedding", "third_embedding"),
        [
            (None, "[0.0, 1.0]"),
            ("not-a-vector", "[0.0, 1.0]"),
            ("[]", "[0.0, 1.0]"),
            ("[NaN, 0.0]", "[0.0, 1.0]"),
            ("[1.0]", "[0.0, 1.0]"),
        ],
    )
    def test_invalid_embedding_falls_back_to_final_score_order(
        self,
        client: TestClient,
        invalid_embedding: object,
        third_embedding: object,
    ) -> None:
        rows = [
            _recommendation("first", 1.0, "[1.0, 0.0]"),
            _recommendation("second", 0.9, invalid_embedding),
            _recommendation("third", 0.8, third_embedding),
        ]
        session = _session_user_then_rows({"id": str(USER_ID)}, rows)
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get(
                f"/v1/recommendations/for-you?user_id={USER_ID}&limit=2"
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        assert [item["project_id"] for item in response.json()] == [
            "first",
            "second",
        ]

    def test_response_payload_excludes_internal_embedding(
        self, client: TestClient
    ) -> None:
        rows = [_recommendation("first", 1.0, "[1.0, 0.0]")]
        session = _session_user_then_rows({"id": str(USER_ID)}, rows)
        app.dependency_overrides[get_db] = lambda: session
        try:
            response = client.get(f"/v1/recommendations/for-you?user_id={USER_ID}")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        assert response.json()[0] == {
            "project_id": "first",
            "title": "First",
            "description": "first description",
            "repo_url": "https://github.com/ost/first",
            "similarity_score": 0.8,
            "preference_score": 0.5,
            "freshness_score": 0.4,
            "popularity_score": 0.2,
            "final_score": 1.0,
        }

        sql = str(session.execute.call_args_list[1].args[0])
        assert "embd_github_project" in sql
