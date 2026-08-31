"""Greedy maximal marginal relevance selection."""

import logging
from collections.abc import Mapping, Sequence
from typing import TypeVar, cast

import numpy as np

logger = logging.getLogger(__name__)

CandidateT = TypeVar("CandidateT", bound=Mapping[str, object])


def _normalized_matrix(candidates: Sequence[CandidateT]) -> np.ndarray | None:
    """Validate and L2-normalize every embedding once.

    Returns None when any embedding is missing, non-numeric, ragged, empty,
    non-finite or zero-norm: cosine similarity is then undefined for the whole
    response, so the caller must fall back to plain relevance order.
    """
    try:
        matrix = np.asarray(
            [candidate.get("embedding") for candidate in candidates], dtype=float
        )
    except (TypeError, ValueError, OverflowError):
        return None
    if matrix.ndim != 2 or matrix.shape[1] == 0 or not np.isfinite(matrix).all():
        return None
    norms = np.linalg.norm(matrix, axis=1)
    if not np.isfinite(norms).all() or (norms == 0).any():
        return None
    return cast("np.ndarray", matrix / norms[:, np.newaxis])


def select_mmr(
    candidates: Sequence[CandidateT],
    limit: int,
    relevance_weight: float = 0.8,
) -> list[CandidateT]:
    """Select candidates by relevance and dissimilarity.

    Falls back to the incoming relevance order when embeddings cannot be used.
    """
    if limit <= 0:
        raise ValueError("limit must be positive")
    if not 0.0 <= relevance_weight <= 1.0:
        raise ValueError("relevance_weight must be between 0 and 1")
    if not candidates:
        return []

    normalized = _normalized_matrix(candidates)
    if normalized is None:
        logger.warning(
            "MMR disabled for this response: invalid or missing project embedding "
            "in %d candidates; falling back to relevance order",
            len(candidates),
        )
        return list(candidates[:limit])

    relevance = np.asarray(
        [float(cast("float", candidate["final_score"])) for candidate in candidates],
        dtype=float,
    )
    diversity_weight = 1.0 - relevance_weight
    remaining = list(range(len(candidates)))
    # Running max cosine similarity to the already selected items, so each
    # candidate is compared only against the newest selection per round.
    max_similarity = np.full(len(candidates), -np.inf)
    selected_indices: list[int] = []

    while remaining and len(selected_indices) < limit:
        if selected_indices:
            penalty = max_similarity[remaining]
        else:
            penalty = np.zeros(len(remaining))
        scores = relevance[remaining] * relevance_weight - diversity_weight * penalty
        # argmax keeps the first of any tie, matching input order.
        best_position = int(np.argmax(scores))
        chosen_index = remaining.pop(best_position)
        selected_indices.append(chosen_index)
        if remaining:
            similarities = normalized[remaining] @ normalized[chosen_index]
            max_similarity[remaining] = np.maximum(
                max_similarity[remaining], similarities
            )

    return [candidates[index] for index in selected_indices]
