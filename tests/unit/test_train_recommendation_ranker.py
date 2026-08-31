from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from dagster import FilesystemIOManager, Output, build_asset_context

from src.linker.assets.ml.core_ml__train_recommendation_ranker import (
    _persist_model,
    core_ml__train_recommendation_ranker,
)
from src.linker.recommendation.ranker import (
    MIN_IMPRESSIONS,
    MIN_POSITIVES,
    RankerTrainingResult,
    train_ranker,
)


def _context(tmp_path: Any) -> Any:
    return build_asset_context(
        resources={"io_manager": FilesystemIOManager(base_dir=str(tmp_path))}
    )


def _feedback_df(n_positive: int, n_negative: int) -> pd.DataFrame:
    rows = [
        {
            "session_key": f"pos-session-{i}",
            "similarity_score": 0.5,
            "preference_score": 0.5,
            "freshness_score": 0.5,
            "popularity_score": 0.9,
            "is_positive": True,
        }
        for i in range(n_positive)
    ] + [
        {
            "session_key": f"neg-session-{i}",
            "similarity_score": 0.5,
            "preference_score": 0.5,
            "freshness_score": 0.5,
            "popularity_score": 0.1,
            "is_positive": False,
        }
        for i in range(n_negative)
    ]
    return pd.DataFrame(rows)


class TestInsufficientData:
    @patch("src.linker.assets.ml.core_ml__train_recommendation_ranker.get_db_cursor")
    def test_returns_not_trained_metadata_without_writing(
        self, mock_get_cursor: MagicMock, tmp_path: Any
    ) -> None:
        feedback_df = _feedback_df(n_positive=1, n_negative=1)
        context = _context(tmp_path)

        output = core_ml__train_recommendation_ranker(context, feedback_df)

        assert isinstance(output, Output)
        assert output.value is None
        assert output.metadata["status"].value == "not_trained"
        assert output.metadata["sample_count"].value == 2
        mock_get_cursor.assert_not_called()

    @patch("src.linker.assets.ml.core_ml__train_recommendation_ranker.get_db_cursor")
    def test_empty_feedback_is_a_successful_no_op(
        self, mock_get_cursor: MagicMock, tmp_path: Any
    ) -> None:
        feedback_df = pd.DataFrame(
            columns=[
                "session_key",
                "similarity_score",
                "preference_score",
                "freshness_score",
                "popularity_score",
                "is_positive",
            ]
        )
        context = _context(tmp_path)

        output = core_ml__train_recommendation_ranker(context, feedback_df)

        assert isinstance(output, Output)
        assert output.metadata["status"].value == "not_trained"
        assert output.metadata["sample_count"].value == 0
        mock_get_cursor.assert_not_called()


class TestQualityGate:
    @patch("src.linker.assets.ml.core_ml__train_recommendation_ranker.get_db_cursor")
    @patch("src.linker.assets.ml.core_ml__train_recommendation_ranker.train_ranker")
    def test_model_worse_than_static_baseline_is_not_persisted(
        self, mock_train_ranker: MagicMock, mock_get_cursor: MagicMock, tmp_path: Any
    ) -> None:
        mock_train_ranker.return_value = RankerTrainingResult(
            trained=False,
            reason=(
                "learned model is worse than the current static score: "
                "NDCG@10 0.300000 < static baseline NDCG@10 1.000000 on the "
                "same held-out sessions"
            ),
            sample_count=200,
            positive_count=20,
            negative_count=180,
            precision_at_10=0.1,
            recall_at_10=1.0,
            ndcg_at_10=0.3,
            baseline_ndcg_at_10=1.0,
        )
        context = _context(tmp_path)

        output = core_ml__train_recommendation_ranker(context, pd.DataFrame())

        assert output.metadata["status"].value == "not_trained"
        assert output.metadata["ndcg_at_10"].value == 0.3
        assert output.metadata["baseline_ndcg_at_10"].value == 1.0
        assert "static baseline" in str(output.metadata["reason"].value)
        mock_get_cursor.assert_not_called()


class TestSuccessfulTraining:
    @patch("src.linker.assets.ml.core_ml__train_recommendation_ranker.get_db_cursor")
    def test_persists_model_and_returns_version_and_metrics(
        self, mock_get_cursor: MagicMock, tmp_path: Any
    ) -> None:
        fake_cur = MagicMock()
        fake_cur.fetchone.return_value = {"version": 3}
        cursor_cm = MagicMock()
        cursor_cm.__enter__.return_value = fake_cur
        cursor_cm.__exit__.return_value = False
        mock_get_cursor.return_value = cursor_cm

        feedback_df = _feedback_df(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )
        context = _context(tmp_path)

        output = core_ml__train_recommendation_ranker(context, feedback_df)

        fake_cur.execute.assert_called_once()
        mock_get_cursor.assert_called_once_with(commit=True)

        assert isinstance(output, Output)
        assert output.metadata["status"].value == "trained"
        assert output.metadata["version"].value == 3
        assert output.metadata["sample_count"].value == MIN_IMPRESSIONS
        assert output.metadata["positive_count"].value == MIN_POSITIVES
        assert output.metadata["precision_at_10"].value is not None
        assert output.metadata["recall_at_10"].value is not None
        assert output.metadata["ndcg_at_10"].value is not None
        assert output.metadata["baseline_ndcg_at_10"].value is not None

    @patch("src.linker.assets.ml.core_ml__train_recommendation_ranker.get_db_cursor")
    def test_insert_receives_coefficients_in_feature_order(
        self, mock_get_cursor: MagicMock, tmp_path: Any
    ) -> None:
        fake_cur = MagicMock()
        fake_cur.fetchone.return_value = {"version": 1}
        cursor_cm = MagicMock()
        cursor_cm.__enter__.return_value = fake_cur
        cursor_cm.__exit__.return_value = False
        mock_get_cursor.return_value = cursor_cm

        feedback_df = _feedback_df(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )
        context = _context(tmp_path)

        core_ml__train_recommendation_ranker(context, feedback_df)

        _query, params = fake_cur.execute.call_args[0]
        coefficients = params[0]
        assert len(coefficients) == 4
        assert all(isinstance(c, float) for c in coefficients)

    @patch("src.linker.assets.ml.core_ml__train_recommendation_ranker.get_db_cursor")
    def test_insert_persists_the_static_baseline_ndcg(
        self, mock_get_cursor: MagicMock, tmp_path: Any
    ) -> None:
        fake_cur = MagicMock()
        fake_cur.fetchone.return_value = {"version": 1}
        cursor_cm = MagicMock()
        cursor_cm.__enter__.return_value = fake_cur
        cursor_cm.__exit__.return_value = False
        mock_get_cursor.return_value = cursor_cm

        feedback_df = _feedback_df(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )
        context = _context(tmp_path)

        core_ml__train_recommendation_ranker(context, feedback_df)

        expected = train_ranker(feedback_df).baseline_ndcg_at_10
        query, params = fake_cur.execute.call_args[0]
        assert "baselineNdcgAt10" in query
        assert expected is not None
        assert params[-1] == pytest.approx(expected)


class TestPersistModelInvariants:
    def test_raises_explicit_error_when_not_trained(self) -> None:
        result = RankerTrainingResult(trained=False, reason="not enough data")
        with pytest.raises(ValueError, match="requires a trained result"):
            _persist_model(MagicMock(), result)

    def test_raises_explicit_error_for_wrong_coefficient_cardinality(self) -> None:
        result = RankerTrainingResult(
            trained=True,
            coefficients=(0.1, 0.2, 0.3),  # type: ignore[arg-type]
            intercept=0.0,
        )
        with pytest.raises(ValueError, match="exactly 4 coefficients"):
            _persist_model(MagicMock(), result)

    def test_raises_explicit_error_for_nan_coefficient(self) -> None:
        result = RankerTrainingResult(
            trained=True,
            coefficients=(0.1, float("nan"), 0.3, 0.4),
            intercept=0.0,
        )
        with pytest.raises(ValueError, match="finite"):
            _persist_model(MagicMock(), result)

    def test_raises_explicit_error_for_infinite_coefficient(self) -> None:
        result = RankerTrainingResult(
            trained=True,
            coefficients=(0.1, 0.2, float("inf"), 0.4),
            intercept=0.0,
        )
        with pytest.raises(ValueError, match="finite"):
            _persist_model(MagicMock(), result)

    def test_raises_explicit_error_for_nan_intercept(self) -> None:
        result = RankerTrainingResult(
            trained=True,
            coefficients=(0.1, 0.2, 0.3, 0.4),
            intercept=float("nan"),
        )
        with pytest.raises(ValueError, match="finite"):
            _persist_model(MagicMock(), result)

    def test_raises_explicit_error_for_infinite_intercept(self) -> None:
        result = RankerTrainingResult(
            trained=True,
            coefficients=(0.1, 0.2, 0.3, 0.4),
            intercept=float("-inf"),
        )
        with pytest.raises(ValueError, match="finite"):
            _persist_model(MagicMock(), result)


class TestAssetWiring:
    def test_asset_key_and_group(self) -> None:
        assert core_ml__train_recommendation_ranker.key.path == [
            "ml",
            "recommendation_ranker_training",
        ]
        group_names = set(
            core_ml__train_recommendation_ranker.group_names_by_key.values()
        )
        assert group_names == {"user_ml"}

    def test_depends_on_feedback_fact(self) -> None:
        upstream_keys = {
            key.path[-1] for key in core_ml__train_recommendation_ranker.dependency_keys
        }
        assert "fct_recommendation_feedback" in upstream_keys
