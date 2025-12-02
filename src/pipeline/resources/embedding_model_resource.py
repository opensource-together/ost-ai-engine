import logging
import os
from dagster import ConfigurableResource
from sentence_transformers import SentenceTransformer
from pydantic import PrivateAttr

class EmbeddingModelResource(ConfigurableResource):
    device: str = "cpu" # cpu usage
    _model: SentenceTransformer = PrivateAttr(default=None)

    def get_model(self):
        # logger = logging.getLogger("dagster")
        if self._model is None:
            home = os.environ.get("SENTENCE_TRANSFORMERS_HOME")
            print(f"EmbeddingModelResource: SENTENCE_TRANSFORMERS_HOME={home}", flush=True)
            
            if home and os.path.exists(home):
                print(f"EmbeddingModelResource: Listing {home}: {os.listdir(home)}", flush=True)
            else:
                print(f"EmbeddingModelResource: {home} does not exist or is not set.", flush=True)

            print("EmbeddingModelResource: Loading model 'sentence-transformers/all-MiniLM-L6-v2'...", flush=True)
            self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=self.device)
            print("EmbeddingModelResource: Model loaded successfully.", flush=True)
        return self._model

    def compute_vector(self, text: str):
        return self.get_model().encode(text, normalize_embeddings=True)