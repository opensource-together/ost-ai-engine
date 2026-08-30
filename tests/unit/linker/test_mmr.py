from copy import deepcopy
from typing import Any

import pytest

from src.linker.recommendation.mmr import select_mmr


def _candidate(
    project_id: str, final_score: float, embedding: list[float]
) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "final_score": final_score,
        "embedding": embedding,
    }


class TestSelectMmr:
    def test_selects_highest_relevance_first(self) -> None:
        candidates = [
            _candidate("lower", 0.7, [0.0, 1.0]),
            _candidate("highest", 0.9, [1.0, 0.0]),
        ]

        selected = select_mmr(candidates, limit=1)

        assert [item["project_id"] for item in selected] == ["highest"]

    def test_diversity_changes_second_selection(self) -> None:
        candidates = [
            _candidate("first", 1.0, [1.0, 0.0]),
            _candidate("similar", 0.9, [1.0, 0.0]),
            _candidate("diverse", 0.8, [0.0, 1.0]),
        ]

        selected = select_mmr(candidates, limit=2)

        assert [item["project_id"] for item in selected] == ["first", "diverse"]

    def test_preserves_input_order_for_exact_ties(self) -> None:
        candidates = [
            _candidate("first", 0.8, [1.0, 0.0]),
            _candidate("second", 0.7, [0.0, 1.0]),
            _candidate("third", 0.7, [0.0, 1.0]),
        ]

        selected = select_mmr(candidates, limit=3)

        assert [item["project_id"] for item in selected] == [
            "first",
            "second",
            "third",
        ]

    def test_does_not_mutate_candidates(self) -> None:
        candidates = [
            _candidate("first", 0.9, [1.0, 0.0]),
            _candidate("second", 0.8, [0.0, 1.0]),
        ]
        original = deepcopy(candidates)

        select_mmr(candidates, limit=2)

        assert candidates == original

    @pytest.mark.parametrize("limit", [0, -1])
    def test_rejects_non_positive_limit(self, limit: int) -> None:
        with pytest.raises(ValueError, match="limit"):
            select_mmr([], limit=limit)

    @pytest.mark.parametrize("relevance_weight", [-0.1, 1.1])
    def test_rejects_weight_outside_unit_interval(
        self, relevance_weight: float
    ) -> None:
        with pytest.raises(ValueError, match="relevance_weight"):
            select_mmr([], limit=1, relevance_weight=relevance_weight)

    def test_returns_available_candidates_when_limit_is_larger(self) -> None:
        candidates = [_candidate("only", 0.9, [1.0, 0.0])]

        selected = select_mmr(candidates, limit=3)

        assert [item["project_id"] for item in selected] == ["only"]
