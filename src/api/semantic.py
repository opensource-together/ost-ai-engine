"""Semantic search: embeds user queries for pgvector cosine similarity."""

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class SemanticSearchService:
    """SentenceTransformer wrapper for semantic project search.

    Loaded at API startup via lifespan and reused per request. Uses the same
    model as the Dagster pipeline for consistent cosine similarity.
    """

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def load(self) -> None:
        """Eager-load the model at lifespan startup to avoid cold-request latency."""
        if self._model is None:
            self._model = SentenceTransformer(self._model_name, device="cpu")

    def encode(self, text: str) -> list[float]:
        """Encode text to a normalized 384-dim vector (ready for cosine similarity)."""
        if self._model is None:
            self.load()
        assert self._model is not None
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()
