from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.linker.recommendation.metrics import ndcg_at_k, precision_at_k, recall_at_k
from src.linker.recommendation.ranker import (
    FEATURE_ORDER,
    MIN_IMPRESSIONS,
    MIN_NEGATIVES,
    MIN_POSITIVES,
    RankerTrainingResult,
    _average_session_metrics,
    _session_holdout_split,
    sigmoid_score,
    train_ranker,
)


def _impressions(
    n_positive: int,
    n_negative: int,
    *,
    incomplete: int = 0,
) -> pd.DataFrame:
    """Build a synthetic, linearly separable impressions frame.

    Positives get a high `popularity_score`, negatives a low one, so a
    logistic regression fit on this data is well defined and deterministic.
    Each row is its own session by default (one impression per session).
    """
    rows: list[dict[str, Any]] = []
    for i in range(n_positive):
        rows.append(
            {
                "session_key": f"pos-session-{i}",
                "similarity_score": 0.5,
                "preference_score": 0.5,
                "freshness_score": 0.5,
                "popularity_score": 0.9,
                "is_positive": True,
            }
        )
    for i in range(n_negative):
        rows.append(
            {
                "session_key": f"neg-session-{i}",
                "similarity_score": 0.5,
                "preference_score": 0.5,
                "freshness_score": 0.5,
                "popularity_score": 0.1,
                "is_positive": False,
            }
        )
    for i in range(incomplete):
        rows.append(
            {
                "session_key": f"incomplete-session-{i}",
                "similarity_score": None,
                "preference_score": 0.5,
                "freshness_score": 0.5,
                "popularity_score": 0.5,
                "is_positive": True,
            }
        )
    return pd.DataFrame(rows)


def _multi_item_sessions(n_sessions: int, items_per_session: int = 10) -> pd.DataFrame:
    """Sessions with one positive candidate among several negatives each.

    Popularity score perfectly separates positive from negative candidates,
    so a well-fit model ranks the positive candidate first within its session.
    """
    rows: list[dict[str, Any]] = []
    for s in range(n_sessions):
        for item in range(items_per_session):
            is_positive = item == 0
            rows.append(
                {
                    "session_key": f"session-{s}",
                    "similarity_score": 0.5,
                    "preference_score": 0.5,
                    "freshness_score": 0.5,
                    "popularity_score": 0.9 if is_positive else 0.1,
                    "is_positive": is_positive,
                }
            )
    return pd.DataFrame(rows)


class TestFeatureOrder:
    def test_declares_exactly_the_four_features_in_order(self) -> None:
        assert FEATURE_ORDER == (
            "similarity_score",
            "preference_score",
            "freshness_score",
            "popularity_score",
        )


class TestTrainRankerThresholds:
    def test_below_minimum_impressions_is_not_trained(self) -> None:
        impressions = _impressions(n_positive=10, n_negative=MIN_IMPRESSIONS - 10 - 1)
        result = train_ranker(impressions)

        assert result.trained is False
        assert result.coefficients is None
        assert result.intercept is None
        assert result.reason is not None

    def test_exactly_minimum_impressions_and_classes_trains(self) -> None:
        impressions = _impressions(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )
        result = train_ranker(impressions)

        assert result.trained is True
        assert result.sample_count == MIN_IMPRESSIONS
        assert result.positive_count == MIN_POSITIVES
        assert result.negative_count == MIN_IMPRESSIONS - MIN_POSITIVES

    def test_below_minimum_positive_class_is_not_trained(self) -> None:
        impressions = _impressions(
            n_positive=MIN_POSITIVES - 1,
            n_negative=MIN_IMPRESSIONS - (MIN_POSITIVES - 1),
        )
        result = train_ranker(impressions)

        assert result.trained is False
        assert result.positive_count == MIN_POSITIVES - 1

    def test_below_minimum_negative_class_is_not_trained(self) -> None:
        impressions = _impressions(
            n_positive=MIN_IMPRESSIONS - (MIN_NEGATIVES - 1),
            n_negative=MIN_NEGATIVES - 1,
        )
        result = train_ranker(impressions)

        assert result.trained is False
        assert result.negative_count == MIN_NEGATIVES - 1

    def test_impressions_missing_feature_snapshots_are_excluded_from_training(
        self,
    ) -> None:
        """Legacy/missing feature snapshots stay metrics rows but never train."""
        impressions = _impressions(
            n_positive=MIN_POSITIVES,
            n_negative=MIN_IMPRESSIONS - MIN_POSITIVES,
            incomplete=5,
        )
        result = train_ranker(impressions)

        assert result.sample_count == MIN_IMPRESSIONS
        assert result.trained is True

    def test_not_trained_result_preserves_static_score_by_omitting_model(
        self,
    ) -> None:
        impressions = _impressions(n_positive=1, n_negative=1)
        result = train_ranker(impressions)

        assert result.trained is False
        assert result.coefficients is None
        assert result.intercept is None
        assert result.precision_at_10 is None
        assert result.recall_at_10 is None
        assert result.ndcg_at_10 is None


class TestSessionHoldoutSplit:
    def test_splits_are_disjoint_and_cover_all_rows(self) -> None:
        impressions = _multi_item_sessions(n_sessions=20, items_per_session=10)
        split = _session_holdout_split(impressions)

        assert split is not None
        train_df, holdout_df = split
        assert len(train_df) + len(holdout_df) == len(impressions)
        assert set(train_df.index).isdisjoint(set(holdout_df.index))

    def test_no_session_crosses_train_and_holdout(self) -> None:
        impressions = _multi_item_sessions(n_sessions=20, items_per_session=10)
        split = _session_holdout_split(impressions)

        assert split is not None
        train_df, holdout_df = split
        train_sessions = set(train_df["session_key"])
        holdout_sessions = set(holdout_df["session_key"])
        assert train_sessions.isdisjoint(holdout_sessions)

    def test_holdout_sessions_are_kept_whole(self) -> None:
        """Every impression of a held-out session appears in the holdout: no
        session is fragmented across the split, so metrics always see the
        complete as-shown session list."""
        impressions = _multi_item_sessions(n_sessions=20, items_per_session=10)
        split = _session_holdout_split(impressions)

        assert split is not None
        _train_df, holdout_df = split
        holdout_sessions = set(holdout_df["session_key"])

        full_counts = (
            impressions[impressions["session_key"].isin(holdout_sessions)]
            .groupby("session_key")
            .size()
            .sort_index()
        )
        holdout_counts = holdout_df.groupby("session_key").size().sort_index()
        pd.testing.assert_series_equal(full_counts, holdout_counts)

    def test_holdout_fraction_is_approximately_twenty_percent_of_sessions(
        self,
    ) -> None:
        impressions = _multi_item_sessions(n_sessions=20, items_per_session=10)
        split = _session_holdout_split(impressions)

        assert split is not None
        _train_df, holdout_df = split
        n_holdout_sessions = holdout_df["session_key"].nunique()
        assert n_holdout_sessions == pytest.approx(0.2 * 20, abs=1)

    def test_training_partition_contains_both_classes(self) -> None:
        impressions = _multi_item_sessions(n_sessions=20, items_per_session=10)
        split = _session_holdout_split(impressions)

        assert split is not None
        train_df, _holdout_df = split
        assert train_df["is_positive"].nunique() == 2

    def test_is_deterministic_across_repeated_calls(self) -> None:
        impressions = _multi_item_sessions(n_sessions=20, items_per_session=10)
        split_a = _session_holdout_split(impressions)
        split_b = _session_holdout_split(impressions)

        assert split_a is not None
        assert split_b is not None
        pd.testing.assert_frame_equal(split_a[0], split_b[0])
        pd.testing.assert_frame_equal(split_a[1], split_b[1])

    def test_returns_none_when_there_are_too_few_sessions_to_split(self) -> None:
        single_session = pd.DataFrame(
            [
                {
                    "session_key": "only-session",
                    "similarity_score": 0.5,
                    "preference_score": 0.5,
                    "freshness_score": 0.5,
                    "popularity_score": 0.9,
                    "is_positive": True,
                },
                {
                    "session_key": "only-session",
                    "similarity_score": 0.5,
                    "preference_score": 0.5,
                    "freshness_score": 0.5,
                    "popularity_score": 0.1,
                    "is_positive": False,
                },
            ]
        )
        assert _session_holdout_split(single_session) is None

    def test_returns_none_when_training_partition_would_miss_a_class(self) -> None:
        """Two sessions, one per label: whichever one lands in train, that
        train partition ends up with only a single class either way."""
        impressions = pd.DataFrame(
            [
                {
                    "session_key": "positive-only-session",
                    "similarity_score": 0.5,
                    "preference_score": 0.5,
                    "freshness_score": 0.5,
                    "popularity_score": 0.9,
                    "is_positive": True,
                },
                {
                    "session_key": "negative-only-session",
                    "similarity_score": 0.5,
                    "preference_score": 0.5,
                    "freshness_score": 0.5,
                    "popularity_score": 0.1,
                    "is_positive": False,
                },
            ]
        )
        assert _session_holdout_split(impressions) is None


class TestAverageSessionMetrics:
    def test_averages_precision_recall_ndcg_across_sessions(self) -> None:
        holdout = pd.DataFrame(
            [
                {"session_key": "s1", "is_positive": True},
                {"session_key": "s1", "is_positive": False},
                {"session_key": "s2", "is_positive": False},
                {"session_key": "s2", "is_positive": True},
            ]
        )
        # s1: positive scored highest (perfect ranking).
        # s2: positive scored lowest (worst ranking).
        scores = np.array([0.9, 0.1, 0.9, 0.1])

        result = _average_session_metrics(holdout, scores)

        assert result is not None
        precision, recall, ndcg = result
        expected_precision = (
            precision_at_k([1, 0], 10) + precision_at_k([0, 1], 10)
        ) / 2
        expected_recall = (recall_at_k([1, 0], 10) + recall_at_k([0, 1], 10)) / 2
        expected_ndcg = (ndcg_at_k([1, 0], 10) + ndcg_at_k([0, 1], 10)) / 2

        assert precision == pytest.approx(expected_precision)
        assert recall == pytest.approx(expected_recall)
        assert ndcg == pytest.approx(expected_ndcg)

    def test_returns_none_for_empty_holdout(self) -> None:
        holdout = pd.DataFrame(columns=["session_key", "is_positive"])
        assert _average_session_metrics(holdout, np.array([])) is None


class TestTrainRankerFit:
    def test_uses_feature_columns_in_declared_order(self) -> None:
        """Shuffling column order in the input frame must not change the fit."""
        impressions = _impressions(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )
        shuffled = impressions[
            [
                "popularity_score",
                "is_positive",
                "similarity_score",
                "session_key",
                "freshness_score",
                "preference_score",
            ]
        ]

        result_a = train_ranker(impressions)
        result_b = train_ranker(shuffled)

        assert result_a.coefficients == pytest.approx(result_b.coefficients)
        assert result_a.intercept == pytest.approx(result_b.intercept)

    def test_training_is_deterministic(self) -> None:
        impressions = _impressions(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )

        result_a = train_ranker(impressions)
        result_b = train_ranker(impressions)

        assert result_a.coefficients == result_b.coefficients
        assert result_a.intercept == result_b.intercept
        assert result_a.precision_at_10 == result_b.precision_at_10
        assert result_a.recall_at_10 == result_b.recall_at_10
        assert result_a.ndcg_at_10 == result_b.ndcg_at_10

    def test_returns_metrics_when_trained(self) -> None:
        impressions = _impressions(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )
        result = train_ranker(impressions)

        assert result.trained is True
        assert result.precision_at_10 is not None
        assert result.recall_at_10 is not None
        assert result.ndcg_at_10 is not None
        assert 0.0 <= result.precision_at_10 <= 1.0
        assert 0.0 <= result.recall_at_10 <= 1.0
        assert 0.0 <= result.ndcg_at_10 <= 1.0

    def test_metrics_are_evaluated_out_of_sample_per_session(self) -> None:
        """A well-separated, whole-session holdout ranks perfectly out-of-sample.

        Because sessions are never fragmented across train/holdout, every
        held-out session keeps its single positive candidate, and a model
        trained on the other 80% of sessions ranks it first every time.
        """
        impressions = _multi_item_sessions(n_sessions=15, items_per_session=10)
        result = train_ranker(impressions)

        assert result.trained is True
        assert result.ndcg_at_10 == pytest.approx(1.0)

    def test_final_coefficients_are_fit_on_all_complete_rows(self) -> None:
        """Persisted coefficients come from a fit on the full complete dataset,
        not only the 80% training split used for evaluation."""
        impressions = _impressions(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )
        result = train_ranker(impressions)
        assert result.trained is True
        assert result.coefficients is not None
        assert result.intercept is not None

        from sklearn.linear_model import LogisticRegression

        model = LogisticRegression(max_iter=1000, class_weight="balanced")
        model.fit(
            impressions[list(FEATURE_ORDER)].to_numpy(dtype=float),
            impressions["is_positive"].astype(int).to_numpy(),
        )

        assert result.coefficients == pytest.approx(tuple(model.coef_[0]))
        assert result.intercept == pytest.approx(model.intercept_[0])


class TestSigmoidScore:
    def test_matches_manual_computation(self) -> None:
        coefficients = (0.1, 0.2, -0.3, 0.4)
        intercept = 0.05
        features = (0.9, 0.8, 0.2, 0.6)

        expected_z = (
            intercept
            + coefficients[0] * features[0]
            + coefficients[1] * features[1]
            + coefficients[2] * features[2]
            + coefficients[3] * features[3]
        )
        expected = 1.0 / (1.0 + math.exp(-expected_z))

        assert sigmoid_score(coefficients, intercept, features) == pytest.approx(
            expected
        )

    def test_zero_intercept_and_coefficients_is_one_half(self) -> None:
        assert sigmoid_score((0.0, 0.0, 0.0, 0.0), 0.0, (1.0, 1.0, 1.0, 1.0)) == 0.5

    def test_result_is_clamped_to_unit_interval(self) -> None:
        score = sigmoid_score((100.0, 0.0, 0.0, 0.0), 0.0, (100.0, 0.0, 0.0, 0.0))
        assert 0.0 <= score <= 1.0

    def test_rejects_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            sigmoid_score((0.1, 0.2), 0.0, (1.0, 1.0, 1.0, 1.0))

    def test_stable_for_large_positive_logit(self) -> None:
        score = sigmoid_score((1000.0,), 0.0, (1.0,))
        assert score == 1.0

    def test_stable_for_large_negative_logit(self) -> None:
        score = sigmoid_score((-1000.0,), 0.0, (1.0,))
        assert 0.0 <= score < 1e-100

    def test_symmetric_for_opposite_signs(self) -> None:
        positive = sigmoid_score((5.0,), 0.0, (1.0,))
        negative = sigmoid_score((-5.0,), 0.0, (1.0,))
        assert positive == pytest.approx(1.0 - negative)

    def test_matches_dbt_learned_path_fixture(self) -> None:
        """Same coefficients/intercept/features as the dbt unit test
        `match_user_recommendation_uses_latest_ranker_model`, so both sides of
        the SQL/Python sigmoid formula are independently exercised on
        identical numbers.
        """
        coefficients = (0.10, 0.20, 0.30, 0.40)
        intercept = 0.05
        features = (0.6, 1.0, 0.9, 0.5)  # similarity, preference, freshness, popularity

        assert sigmoid_score(coefficients, intercept, features) == pytest.approx(
            0.6856801139382539
        )

    def test_matches_fitted_model_prediction(self) -> None:
        """The manual sigmoid formula must reproduce sklearn's own prediction.

        This is exactly the formula dbt applies in SQL for the learned score,
        fit with the same settings (max_iter, class_weight) as production.
        """
        impressions = _impressions(
            n_positive=MIN_POSITIVES, n_negative=MIN_IMPRESSIONS - MIN_POSITIVES
        )
        result = train_ranker(impressions)
        assert result.trained is True
        assert result.coefficients is not None
        assert result.intercept is not None

        row = impressions.iloc[0]
        features = tuple(float(row[name]) for name in FEATURE_ORDER)

        from sklearn.linear_model import LogisticRegression

        model = LogisticRegression(max_iter=1000, class_weight="balanced")
        model.fit(
            impressions[list(FEATURE_ORDER)].to_numpy(dtype=float),
            impressions["is_positive"].astype(int).to_numpy(),
        )
        expected = float(model.predict_proba([features])[0][1])

        assert sigmoid_score(
            result.coefficients, result.intercept, features
        ) == pytest.approx(expected)


class TestRankerTrainingResultShape:
    def test_not_trained_result_can_be_constructed_directly(self) -> None:
        result = RankerTrainingResult(trained=False, reason="not enough data")
        assert result.trained is False
        assert result.sample_count == 0
