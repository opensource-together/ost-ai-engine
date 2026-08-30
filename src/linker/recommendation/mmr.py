"""Greedy maximal marginal relevance selection."""

from collections.abc import Mapping, Sequence
from typing import TypeVar, cast

import numpy as np

CandidateT = TypeVar("CandidateT", bound=Mapping[str, object])


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right)))


def select_mmr(
    candidates: Sequence[CandidateT],
    limit: int,
    relevance_weight: float = 0.8,
) -> list[CandidateT]:
    """Select candidates by relevance and dissimilarity."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    if not 0.0 <= relevance_weight <= 1.0:
        raise ValueError("relevance_weight must be between 0 and 1")

    embeddings = [
        np.asarray(
            cast("Sequence[float]", candidate["embedding"]),
            dtype=float,
        )
        for candidate in candidates
    ]
    remaining = list(range(len(candidates)))
    selected_indices: list[int] = []

    while remaining and len(selected_indices) < limit:
        best_position = 0
        best_score = float("-inf")
        for position, candidate_index in enumerate(remaining):
            relevance = float(cast("float", candidates[candidate_index]["final_score"]))
            max_similarity = max(
                (
                    _cosine_similarity(
                        embeddings[candidate_index], embeddings[selected_index]
                    )
                    for selected_index in selected_indices
                ),
                default=0.0,
            )
            score = (
                relevance_weight * relevance - (1.0 - relevance_weight) * max_similarity
            )
            if score > best_score:
                best_position = position
                best_score = score

        selected_indices.append(remaining.pop(best_position))

    return [candidates[index] for index in selected_indices]
