"""
Dagster resource pour service d'embedding optimisé 4GB RAM.
"""

import gc
import hashlib
import time
from typing import Any

import numpy as np
import torch
from dagster import ConfigurableResource
from sentence_transformers import SentenceTransformer

from src.infrastructure.cache import cache_service
from src.infrastructure.logger import log
from src.infrastructure.config import settings


class EmbeddingResource(ConfigurableResource):
    """Resource Dagster pour embeddings avec all-MiniLM-L6-v2."""
    
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_batch_size: int = 32
    cache_ttl: int = 86400  # 24h
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._model: SentenceTransformer | None = None
        
    def _load_model(self) -> SentenceTransformer:
        """Load model with RAM optimizations."""
        if self._model is None:
            log.info(f"🤖 Loading {self.model_name}")
            model = SentenceTransformer(
                self.model_name,
                device='cpu',
                cache_folder=settings.MODEL_CACHE_PATH
            )
            torch.set_num_threads(2)
            
            # Utiliser object.__setattr__ pour contourner le frozen ConfigurableResource
            object.__setattr__(self, '_model', model)
            
            # Calculate actual model size
            import sys
            model_size_mb = sum(p.numel() * p.element_size() for p in self._model.parameters()) / (1024 * 1024)
            log.info(f"✅ Model loaded ({model_size_mb:.1f}MB)")
        return self._model
    
    def _unload_model(self):
        """Free RAM."""
        if self._model is not None:
            # Utiliser object.__setattr__ pour contourner le frozen ConfigurableResource
            object.__setattr__(self, '_model', None)
            gc.collect()
            log.info("🗑️ Model unloaded")
    
    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """Encode batch avec cache Redis."""
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        
        cleaned_texts = [text.strip() if text else "" for text in texts]
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache
        for i, text in enumerate(cleaned_texts):
            if not text:
                embeddings.append(np.zeros(384, dtype=np.float32))
                continue
                
            cache_key = f"embed:{hashlib.md5(text.encode()).hexdigest()[:16]}"
            cached = cache_service.get(cache_key, namespace="embeddings")
            
            if cached is not None:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                uncached_indices.append(i)
                uncached_texts.append(text)
        
        # Encode uncached
        if uncached_texts:
            log.info(f"🔢 Encoding {len(uncached_texts)} texts")
            model = self._load_model()
            
            new_embeddings = model.encode(
                uncached_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=self.max_batch_size,
                show_progress_bar=False
            )
            
            # Insert new embeddings and cache
            for idx, embedding in zip(uncached_indices, new_embeddings):
                embeddings[idx] = embedding.astype(np.float32)
                cache_key = f"embed:{hashlib.md5(cleaned_texts[idx].encode()).hexdigest()[:16]}"
                cache_service.set(cache_key, embedding, ttl=self.cache_ttl, namespace="embeddings")
            
            self._unload_model()
        
        return np.array(embeddings, dtype=np.float32)
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode texte unique."""
        return self.encode_batch([text])[0]


# Resource factory
def embedding_service():
    return EmbeddingResource()
