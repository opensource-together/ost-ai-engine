import math
from collections.abc import Sequence


def _validate_k(k: int) -> None:
    if k <= 0:
        raise ValueError("k must be greater than 0")


def precision_at_k(relevance: Sequence[int], k: int) -> float:
    """Return positives divided by observed items in the first k positions."""
    _validate_k(k)
    observed = relevance[:k]
    if not observed:
        return 0.0
    return sum(observed) / len(observed)


def recall_at_k(relevance: Sequence[int], k: int) -> float:
    """Return top-k positives divided by all observed positives."""
    _validate_k(k)
    total_positives = sum(relevance)
    if total_positives == 0:
        return 0.0
    return sum(relevance[:k]) / total_positives


def ndcg_at_k(relevance: Sequence[int], k: int) -> float:
    """Return binary discounted cumulative gain normalized at k."""
    _validate_k(k)
    total_positives = sum(relevance)
    if total_positives == 0:
        return 0.0

    dcg = sum(
        label / math.log2(position + 2) for position, label in enumerate(relevance[:k])
    )
    ideal_count = min(total_positives, k)
    ideal_dcg = sum(1.0 / math.log2(position + 2) for position in range(ideal_count))
    return dcg / ideal_dcg
