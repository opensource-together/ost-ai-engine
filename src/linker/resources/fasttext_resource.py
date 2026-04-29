"""FastText language-detection resource for Dagster (singleton)."""

import logging
import os
import warnings
from typing import Any

from dagster import ConfigurableResource
from pydantic import PrivateAttr

logger = logging.getLogger(__name__)


class FastTextModelResource(ConfigurableResource):
    """Loads `model_path` once; used by assets that need language detection."""

    model_path: str = "models/lid.176.ftz"
    _model: Any = PrivateAttr(default=None)

    @property
    def model(self) -> Any:
        if self._model is None:
            try:
                import fasttext  # type: ignore[import-untyped]
            except ImportError as e:
                raise ImportError(
                    "fasttext is required for language detection. "
                    "Use: uv sync (includes fasttext)."
                ) from e

            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"FastText model not found at: {self.model_path}. "
                    f"Expected lid.176.ftz model file."
                )

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                logger.info("Loading FastText model from %s", self.model_path)
                self._model = fasttext.load_model(self.model_path)
                logger.info("FastText model loaded")

        return self._model

    def predict(self, text: str, k: int = 1) -> Any:
        """Predict language(s) for given text.

        Args:
            text: Input text to detect language from
            k: Number of top predictions to return

        Returns:
            Tuple of (labels, probabilities)
        """
        return self.model.predict(text, k=k)
