"""FastText model resource for Dagster pipeline.

Provides a singleton fastText language detection model that is loaded once
and reused across all assets.
"""

import os
from typing import Any

from dagster import ConfigurableResource
from pydantic import PrivateAttr


class FastTextModelResource(ConfigurableResource):
    """Wrapper for fastText language detection model.

    Loads the model once during initialization and provides it to all assets
    that require language detection functionality.
    """

    model_path: str = "models/lid.176.ftz"
    _model: Any = PrivateAttr(default=None)

    @property
    def model(self) -> Any:
        """Lazy-load and return the fastText model.

        Returns:
            fasttext model instance

        Raises:
            ImportError: if fasttext package is not installed
            FileNotFoundError: if model file doesn't exist
        """
        if self._model is None:
            try:
                import fasttext  # type: ignore[import-untyped]
            except ImportError as e:
                raise ImportError(
                    "fasttext package is required for language detection. "
                    "Install it with: poetry add fasttext"
                ) from e

            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"FastText model not found at: {self.model_path}. "
                    f"Expected lid.176.ftz model file."
                )

            # Suppress fastText warnings during model loading
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                print(
                    f"FastTextModelResource: Loading model from {self.model_path}...",
                    flush=True,
                )
                self._model = fasttext.load_model(self.model_path)
                print("FastTextModelResource: Model loaded successfully.", flush=True)

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
