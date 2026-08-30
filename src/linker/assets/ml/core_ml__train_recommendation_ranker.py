"""Trains and persists the logistic recommendation ranker from feedback."""

from typing import Any

import numpy as np
import pandas as pd
from dagster import AssetExecutionContext, AssetIn, AssetKey, Output, asset

from src.linker.recommendation.ranker import RankerTrainingResult, train_ranker
from src.services.python.db import get_db_cursor

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

_INSERT_MODEL_QUERY = """
    INSERT INTO "ml"."recommendation_ranker_model"
        ("id", "coefficients", "intercept", "sampleCount", "positiveCount",
         "negativeCount", "precisionAt10", "recallAt10", "ndcgAt10")
    VALUES (uuid_generate_v4(), %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING "version"
"""


def _persist_model(cur: Any, result: RankerTrainingResult) -> int:
    """Insert one immutable model version row and return its version number."""
    if result.coefficients is None or result.intercept is None:
        raise ValueError(
            "invariant violated: _persist_model requires a trained result with "
            "coefficients and an intercept"
        )
    if len(result.coefficients) != 4:
        raise ValueError(
            "invariant violated: expected exactly 4 coefficients "
            f"(similarity, preference, freshness, popularity), got "
            f"{len(result.coefficients)}"
        )
    if not (np.isfinite(result.coefficients).all() and np.isfinite(result.intercept)):
        raise ValueError(
            "invariant violated: coefficients and intercept must all be finite "
            f"(no NaN/Infinity), got coefficients={result.coefficients!r}, "
            f"intercept={result.intercept!r}"
        )
    cur.execute(
        _INSERT_MODEL_QUERY,
        (
            list(result.coefficients),
            result.intercept,
            result.sample_count,
            result.positive_count,
            result.negative_count,
            result.precision_at_10,
            result.recall_at_10,
            result.ndcg_at_10,
        ),
    )
    row = cur.fetchone()
    return int(row["version"])


@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    # Deliberately NOT `AssetKey(["ml", "recommendation_ranker_model"])`: dbt's
    # default source-key derivation would then treat this asset's output as
    # the same node `match_user_recommendation` depends on via
    # `source('ml', 'recommendation_ranker_model')`, wiring a hard Dagster
    # dependency edge and risking a future cycle as the graph evolves (see
    # dbt/models/sources.yml for the matching source-side rationale). The
    # persisted table is instead picked up by plain SQL on the next scheduled
    # dbt run, not by a Dagster asset dependency edge.
    key=AssetKey(["ml", "recommendation_ranker_training"]),
    ins={
        "feedback_df": AssetIn(key=AssetKey(["public", "fct_recommendation_feedback"]))
    },
    group_name="user_ml",
    required_resource_keys={"io_manager"},
)
def core_ml__train_recommendation_ranker(
    context: AssetExecutionContext,
    feedback_df: pd.DataFrame,
) -> Output[None]:
    """Trains the logistic ranker from `fct_recommendation_feedback`.

    Persists one immutable version row to `ml.recommendation_ranker_model` on
    success. Insufficient data is a successful no-op: no row is written and
    the current static dbt score is preserved on the next
    `match_user_recommendation` run.
    """
    result = train_ranker(feedback_df)

    if not result.trained:
        context.log.info(f"Ranker not trained: {result.reason}")
        return Output(
            value=None,
            metadata={
                "status": "not_trained",
                "reason": result.reason,
                "sample_count": result.sample_count,
                "positive_count": result.positive_count,
                "negative_count": result.negative_count,
            },
        )

    with get_db_cursor(commit=True) as cur:
        version = _persist_model(cur, result)

    context.log.info(f"Persisted recommendation ranker model version {version}")
    return Output(
        value=None,
        metadata={
            "status": "trained",
            "version": version,
            "sample_count": result.sample_count,
            "positive_count": result.positive_count,
            "negative_count": result.negative_count,
            "precision_at_10": result.precision_at_10,
            "recall_at_10": result.recall_at_10,
            "ndcg_at_10": result.ndcg_at_10,
        },
    )
