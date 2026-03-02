import logging
from dagster import ConfigurableResource
from sentence_transformers import SentenceTransformer
from pydantic import PrivateAttr

class SentenceTransformerResource(ConfigurableResource):
    """
    Resource for SentenceTransformer model to compute text embeddings.
    """
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cpu"
    _model: SentenceTransformer = PrivateAttr(default=None)

    def get_model(self) -> SentenceTransformer:
        if self._model is None:
            # logger = logging.getLogger("dagster")
            # logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            print(f"Loading SentenceTransformer model: {self.model_name} on {self.device}", flush=True)
            self._model = SentenceTransformer(self.model_name, device=self.device)
            print("Model loaded successfully.", flush=True)
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
