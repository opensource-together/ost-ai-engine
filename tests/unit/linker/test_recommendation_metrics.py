import math

import pytest

from src.linker.recommendation.metrics import ndcg_at_k, precision_at_k, recall_at_k


class TestPrecisionAtK:
    def test_uses_observed_items_when_fewer_than_k(self) -> None:
        assert precision_at_k([1, 0, 1], 5) == pytest.approx(2 / 3)

    def test_empty_labels_return_zero(self) -> None:
        assert precision_at_k([], 5) == 0.0

    def test_rejects_non_positive_k(self) -> None:
        with pytest.raises(ValueError, match="k must be greater than 0"):
            precision_at_k([1], 0)


class TestRecallAtK:
    def test_uses_all_observed_positives_as_denominator(self) -> None:
        assert recall_at_k([1, 0, 1, 1], 2) == pytest.approx(1 / 3)

    def test_no_positives_return_zero(self) -> None:
        assert recall_at_k([0, 0], 2) == 0.0

    def test_rejects_non_positive_k(self) -> None:
        with pytest.raises(ValueError, match="k must be greater than 0"):
            recall_at_k([1], -1)


class TestNdcgAtK:
    def test_binary_discounted_gain(self) -> None:
        expected = (1.0 + 1.0 / math.log2(4)) / (1.0 + 1.0 / math.log2(3))
        assert ndcg_at_k([1, 0, 1], 3) == pytest.approx(expected)

    def test_empty_labels_return_zero(self) -> None:
        assert ndcg_at_k([], 5) == 0.0

    def test_rejects_non_positive_k(self) -> None:
        with pytest.raises(ValueError, match="k must be greater than 0"):
            ndcg_at_k([1], 0)
