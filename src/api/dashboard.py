"""Load recommendation quality KPIs for the business dashboard."""

import html
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from src.api.row_mapping import mapping_row_first
from src.api.schemas import DashboardOut, RankerMetricsOut

_CORE_SQL = """
SELECT
    (SELECT COUNT(*)::int FROM public."user") AS user_count,
    (SELECT COUNT(*)::int FROM public."Project") AS project_count,
    (SELECT COUNT(*)::int FROM public.project_bookmark) AS bookmark_count,
    (SELECT COUNT(*)::int FROM public.match_user_recommendation)
        AS personalized_pairs,
    (SELECT COUNT(*)::int FROM public.recommendation_event
        WHERE "eventType" = 'SHOWN') AS shown_events,
    (SELECT COUNT(*)::int FROM public.recommendation_event
        WHERE "eventType" IN ('CLICKED', 'STARRED_AFTER_RECO'))
        AS positive_events
"""

_FEEDBACK_SQL = """
SELECT
    COUNT(*)::int AS feedback_impressions,
    COUNT(*) FILTER (WHERE is_positive)::int AS feedback_positives
FROM public.fct_recommendation_feedback
"""

_RANKER_SQL = """
SELECT
    version,
    "sampleCount" AS sample_count,
    "positiveCount" AS positive_count,
    "negativeCount" AS negative_count,
    "precisionAt10" AS precision_at_10,
    "recallAt10" AS recall_at_10,
    "ndcgAt10" AS ndcg_at_10,
    "baselineNdcgAt10" AS baseline_ndcg_at_10,
    "createdAt" AS created_at
FROM ml.recommendation_ranker_model
ORDER BY version DESC
LIMIT 1
"""


def _safe_row(db: Session, sql: str) -> dict[str, Any] | None:
    try:
        return mapping_row_first(db.execute(text(sql)))
    except ProgrammingError:
        db.rollback()
        return None


def load_dashboard(db: Session) -> DashboardOut:
    """Read catalog, event, feedback and ranker counts from Postgres."""
    core = _safe_row(db, _CORE_SQL) or {}
    feedback = _safe_row(db, _FEEDBACK_SQL) or {}
    ranker_row = _safe_row(db, _RANKER_SQL)
    ranker = RankerMetricsOut.model_validate(ranker_row) if ranker_row else None
    return DashboardOut(
        user_count=int(core.get("user_count") or 0),
        project_count=int(core.get("project_count") or 0),
        bookmark_count=int(core.get("bookmark_count") or 0),
        shown_events=int(core.get("shown_events") or 0),
        positive_events=int(core.get("positive_events") or 0),
        personalized_pairs=int(core.get("personalized_pairs") or 0),
        feedback_impressions=int(feedback.get("feedback_impressions") or 0),
        feedback_positives=int(feedback.get("feedback_positives") or 0),
        ranker=ranker,
    )


def _card(label: str, value: str) -> str:
    return (
        f'<article class="card"><p class="label">{html.escape(label)}</p>'
        f'<p class="value">{html.escape(value)}</p></article>'
    )


def render_dashboard_html(snapshot: DashboardOut) -> str:
    """Server-rendered KPI page; no client-side fetch."""
    ranker = snapshot.ranker
    if ranker is None:
        ranker_cards = _card("Learned ranker", "not trained")
    else:
        ranker_cards = "".join(
            [
                _card("Ranker version", str(ranker.version)),
                _card("Precision@10", f"{ranker.precision_at_10:.3f}"),
                _card("Recall@10", f"{ranker.recall_at_10:.3f}"),
                _card("NDCG@10", f"{ranker.ndcg_at_10:.3f}"),
                _card("Baseline NDCG@10", f"{ranker.baseline_ndcg_at_10:.3f}"),
            ]
        )
    cards = "".join(
        [
            _card("Users", str(snapshot.user_count)),
            _card("Projects", str(snapshot.project_count)),
            _card("Bookmarks", str(snapshot.bookmark_count)),
            _card("Personalized pairs", str(snapshot.personalized_pairs)),
            _card("SHOWN events", str(snapshot.shown_events)),
            _card("Clicks / stars after reco", str(snapshot.positive_events)),
            _card("Labeled impressions", str(snapshot.feedback_impressions)),
            _card("Positive labels", str(snapshot.feedback_positives)),
            ranker_cards,
        ]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>OST Linker recommendations</title>
  <style>
    body {{
      font-family: sans-serif; margin: 1.5rem;
      background: #0f1419; color: #e7ecf3;
    }}
    h1 {{ font-size: 1.4rem; }}
    .grid {{
      display: grid; gap: 1rem;
      grid-template-columns: repeat(auto-fill, minmax(12rem, 1fr));
    }}
    .card {{ background: #1b2430; padding: 1rem; border-radius: 0.5rem; }}
    .label {{ margin: 0; color: #9aa8b8; font-size: 0.85rem; }}
    .value {{ margin: 0.35rem 0 0; font-size: 1.6rem; }}
  </style>
</head>
<body>
  <h1>Recommendation quality</h1>
  <div class="grid">{cards}</div>
</body>
</html>
"""
