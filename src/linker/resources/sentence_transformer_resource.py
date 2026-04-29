import logging

from dagster import ConfigurableResource
from pydantic import PrivateAttr
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SentenceTransformerResource(ConfigurableResource):
    """
    Resource for SentenceTransformer model to compute text embeddings.
    """

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cpu"
    _model: SentenceTransformer | None = PrivateAttr(default=None)

    def get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(
                "Loading SentenceTransformer model %s on %s",
                self.model_name,
                self.device,
            )
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("SentenceTransformer model loaded")
        return self._model

    def encode(self, text: str) -> list[float]:
        """
        Encodes a single string into a vector.
        """
        model = self.get_model()
        # normalize_embeddings=True is good for cosine similarity
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Encodes a list of strings into vectors.
        """
        model = self.get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return [vec.tolist() for vec in embeddings]
