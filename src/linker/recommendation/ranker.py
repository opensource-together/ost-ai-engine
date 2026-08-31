"""Logistic regression ranker over labeled recommendation feedback impressions."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit

from src.linker.recommendation.metrics import ndcg_at_k, precision_at_k, recall_at_k

FEATURE_ORDER: tuple[str, str, str, str] = (
    "similarity_score",
    "preference_score",
    "freshness_score",
    "popularity_score",
)

# Static weighted blend currently in production, in FEATURE_ORDER order. Must
# stay in sync with w_similarity/w_preference/w_freshness/w_popularity in
# dbt/dbt_project.yml: it is the baseline a learned model has to beat.
STATIC_SCORE_WEIGHTS: tuple[float, float, float, float] = (0.40, 0.35, 0.15, 0.10)

MIN_IMPRESSIONS = 100
MIN_POSITIVES = 10
MIN_NEGATIVES = 10
_METRIC_K = 10
_LABEL_COLUMN = "is_positive"
_SESSION_COLUMN = "session_key"
_HOLDOUT_FRACTION = 0.2
_SPLIT_RANDOM_STATE = 42


@dataclass(frozen=True)
class RankerTrainingResult:
    """Outcome of a single ranker training attempt.

    `trained=False` means the current static score must be preserved as-is.
    """

    trained: bool
    reason: str | None = None
    coefficients: tuple[float, float, float, float] | None = None
    intercept: float | None = None
    sample_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    precision_at_10: float | None = None
    recall_at_10: float | None = None
    ndcg_at_10: float | None = None
    baseline_ndcg_at_10: float | None = None


def _complete_impressions(impressions: pd.DataFrame) -> pd.DataFrame:
    """Keep rows where all four features, the label, and the session are present."""
    required = [*FEATURE_ORDER, _LABEL_COLUMN, _SESSION_COLUMN]
    return impressions.dropna(subset=required)


def _binary_labels(frame: pd.DataFrame) -> np.ndarray:
    return frame[_LABEL_COLUMN].astype(bool).astype(int).to_numpy()


def _feature_matrix(frame: pd.DataFrame) -> np.ndarray:
    return frame[list(FEATURE_ORDER)].to_numpy(dtype=float)


def _ranked_relevance(labels: np.ndarray, scores: np.ndarray) -> list[int]:
    """Sort binary labels by descending predicted score for ranking metrics."""
    order = np.argsort(-scores, kind="stable")
    return [int(label) for label in labels[order]]


def _fit_logistic(x: np.ndarray, y: np.ndarray) -> LogisticRegression:
    """Fit with class balancing so imbalanced impressions don't bias training."""
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(x, y)
    return model


def _session_holdout_split(
    complete: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Deterministic whole-session 80/20 holdout split.

    Splits by `session_key` (via `GroupShuffleSplit`) so every impression in
    a session lands on the same side: no session is fragmented across train
    and holdout, so ranking metrics are always computed over complete,
    as-shown session lists. Returns None when a valid split cannot be
    produced: too few sessions to split, an empty partition, or a training
    partition missing a label class.
    """
    groups = complete[_SESSION_COLUMN].to_numpy()
    if len(np.unique(groups)) < 2:
        return None

    splitter = GroupShuffleSplit(
        n_splits=1, test_size=_HOLDOUT_FRACTION, random_state=_SPLIT_RANDOM_STATE
    )
    try:
        train_positions, holdout_positions = next(
            splitter.split(complete, groups=groups)
        )
    except ValueError:
        return None

    train_df = complete.iloc[train_positions]
    holdout_df = complete.iloc[holdout_positions]
    if train_df.empty or holdout_df.empty:
        return None
    if len(np.unique(_binary_labels(train_df))) < 2:
        return None
    return train_df, holdout_df


def _average_session_metrics(
    holdout: pd.DataFrame, scores: np.ndarray
) -> tuple[float, float, float] | None:
    """Average Precision/Recall/NDCG@10 per session over holdout impressions.

    Ranking metrics are computed within each session (a single shown list)
    and averaged across sessions, rather than pooled globally. Sessions
    without a single positive item are skipped: as in a conventional IR query
    set, a query with no relevant document has no defined ranking quality, and
    counting it as zero would only dilute the average with sessions no ranker
    can improve. Returns None when no session is evaluable.
    """
    if len(holdout) == 0:
        return None
    scored = holdout.assign(_predicted_score=scores)

    precisions: list[float] = []
    recalls: list[float] = []
    ndcgs: list[float] = []
    for _session_key, group in scored.groupby(_SESSION_COLUMN, sort=False):
        labels = _binary_labels(group)
        if labels.sum() == 0:
            continue
        relevance = _ranked_relevance(labels, group["_predicted_score"].to_numpy())
        precisions.append(precision_at_k(relevance, _METRIC_K))
        recalls.append(recall_at_k(relevance, _METRIC_K))
        ndcgs.append(ndcg_at_k(relevance, _METRIC_K))

    if not precisions:
        return None
    return (
        sum(precisions) / len(precisions),
        sum(recalls) / len(recalls),
        sum(ndcgs) / len(ndcgs),
    )


def _static_scores(frame: pd.DataFrame) -> np.ndarray:
    """Score rows with the static weighted blend dbt applies today."""
    return cast(
        "np.ndarray",
        _feature_matrix(frame) @ np.asarray(STATIC_SCORE_WEIGHTS, dtype=float),
    )


def train_ranker(impressions: pd.DataFrame) -> RankerTrainingResult:
    """Fit a logistic regression ranker from labeled recommendation impressions.

    Requires at least 100 complete impressions with at least 10 positive and
    10 negative labels; otherwise returns a not-trained result so callers keep
    the current static score unchanged.

    Evaluation is out-of-sample: a deterministic whole-session 80/20 holdout
    is split off (no session is fragmented across train/holdout), an
    evaluation model is fit on the 80% training split only, and
    Precision/Recall/NDCG@10 are computed per complete held-out session and
    averaged across sessions. The coefficients actually persisted are then
    fit separately on all complete rows (train + holdout combined).

    Quality gate: the current static weighted blend is scored on the exact
    same held-out sessions, and a learned model whose NDCG@10 is below that
    baseline is rejected (not-trained no-op) instead of being persisted. The
    comparison is relative to the live baseline, so no arbitrary metric
    threshold is involved.

    Known limitation: labels come from impressions the current ranker chose
    and ordered, with no exploration arm and no position-bias correction, so
    the model is fit on click feedback biased towards what was already shown
    high in the list. The baseline gate bounds the damage; it does not remove
    the bias.
    """
    complete = _complete_impressions(impressions)
    sample_count = len(complete)
    positive_count = int(_binary_labels(complete).sum()) if sample_count else 0
    negative_count = sample_count - positive_count

    if (
        sample_count < MIN_IMPRESSIONS
        or positive_count < MIN_POSITIVES
        or negative_count < MIN_NEGATIVES
    ):
        return RankerTrainingResult(
            trained=False,
            reason=(
                f"insufficient data: {sample_count} complete impressions "
                f"({positive_count} positive, {negative_count} negative); "
                f"requires >= {MIN_IMPRESSIONS} complete impressions, "
                f">= {MIN_POSITIVES} positive, and >= {MIN_NEGATIVES} negative"
            ),
            sample_count=sample_count,
            positive_count=positive_count,
            negative_count=negative_count,
        )

    split = _session_holdout_split(complete)
    if split is None:
        return RankerTrainingResult(
            trained=False,
            reason=(
                "could not build a valid whole-session 80/20 holdout split "
                f"from {sample_count} complete impressions"
            ),
            sample_count=sample_count,
            positive_count=positive_count,
            negative_count=negative_count,
        )
    train_df, holdout_df = split

    eval_model = _fit_logistic(_feature_matrix(train_df), _binary_labels(train_df))
    holdout_scores = eval_model.predict_proba(_feature_matrix(holdout_df))[:, 1]
    session_metrics = _average_session_metrics(holdout_df, holdout_scores)
    if session_metrics is None:
        return RankerTrainingResult(
            trained=False,
            reason=(
                "session holdout produced no evaluable session: no held-out "
                "session contains a positive impression"
            ),
            sample_count=sample_count,
            positive_count=positive_count,
            negative_count=negative_count,
        )
    precision, recall, ndcg = session_metrics

    # Same held-out sessions, scored with the live static blend.
    baseline_metrics = _average_session_metrics(holdout_df, _static_scores(holdout_df))
    baseline_ndcg = baseline_metrics[2] if baseline_metrics is not None else None
    if baseline_ndcg is not None and ndcg < baseline_ndcg:
        return RankerTrainingResult(
            trained=False,
            reason=(
                f"learned model is worse than the current static score: "
                f"NDCG@10 {ndcg:.6f} < static baseline NDCG@10 "
                f"{baseline_ndcg:.6f} on the same held-out sessions"
            ),
            sample_count=sample_count,
            positive_count=positive_count,
            negative_count=negative_count,
            precision_at_10=precision,
            recall_at_10=recall,
            ndcg_at_10=ndcg,
            baseline_ndcg_at_10=baseline_ndcg,
        )

    final_model = _fit_logistic(_feature_matrix(complete), _binary_labels(complete))
    c0, c1, c2, c3 = (float(c) for c in final_model.coef_[0])

    return RankerTrainingResult(
        trained=True,
        coefficients=(c0, c1, c2, c3),
        intercept=float(final_model.intercept_[0]),
        sample_count=sample_count,
        positive_count=positive_count,
        negative_count=negative_count,
        precision_at_10=precision,
        recall_at_10=recall,
        ndcg_at_10=ndcg,
        baseline_ndcg_at_10=baseline_ndcg,
    )


def sigmoid_score(
    coefficients: Sequence[float], intercept: float, features: Sequence[float]
) -> float:
    """Compute sigmoid(intercept + sum(coeff_i * feature_i)), clamped to [0, 1].

    Uses a numerically stable formulation for both large-positive and
    large-negative logits, and clamps the logit to [-500, 500] beforehand.
    Mirrors the SQL expression dbt applies when a persisted model is present.
    """
    if len(coefficients) != len(features):
        raise ValueError("coefficients and features must have the same length")
    z = intercept + sum(c * f for c, f in zip(coefficients, features, strict=True))
    z = max(-500.0, min(500.0, z))
    if z >= 0:
        score = 1.0 / (1.0 + math.exp(-z))
    else:
        exp_z = math.exp(z)
        score = exp_z / (1.0 + exp_z)
    return min(1.0, max(0.0, score))
