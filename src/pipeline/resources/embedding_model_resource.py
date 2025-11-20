from dagster import ConfigurableResource
from sentence_transformers import SentenceTransformer
from pydantic import PrivateAttr

class BGEModelResource(ConfigurableResource):
    device: str = "cpu" # cpu usage
    _model: SentenceTransformer = PrivateAttr(default=None)

    def get_model(self):
        if self._model is None:
            self._model = SentenceTransformer("BAAI/bge-m3", device=self.device)
        return self._model

    def compute_vector(self, text: str):
        return self.get_model().encode(text, normalize_embeddings=True)