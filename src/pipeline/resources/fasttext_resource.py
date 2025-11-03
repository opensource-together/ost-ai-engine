"""FastText model resource for Dagster pipeline.

Provides a singleton fastText language detection model that is loaded once
and reused across all assets, avoiding repeated disk I/O and model initialization.

## Why use a resource?

Loading the fastText model from disk is expensive (~100MB file, takes ~1s).
By making it a Dagster resource:
1. **Loaded once** at pipeline initialization (not per asset execution)
2. **Shared across assets** that need language detection
3. **Proper lifecycle management** by Dagster
4. **Easy testing** with mock resources
5. **Clear dependencies** via `required_resource_keys`

## Configuration

The resource expects the model path to be configured in Dagster definitions.
Default path in Docker: `/app/models/lid.176.ftz`

## Example Usage

```python
@asset(required_resource_keys={"fasttext_model"})
def detect_languages(context):
    fasttext = context.resources.fasttext_model
    
    # Predict single language
    labels, probs = fasttext.predict("Hello world", k=1)
    # Returns: (['__label__en'], [0.99])
    
    # Predict top-3 languages
    labels, probs = fasttext.predict("Mixed text", k=3)
    # Returns: (['__label__en', '__label__fr', '__label__es'], [0.7, 0.2, 0.1])
```
"""
import os
from dagster import resource, InitResourceContext
from typing import Optional


class FastTextModelResource:
    """Wrapper for fastText language detection model.
    
    Loads the model once during initialization and provides it to all assets
    that require language detection functionality.
    """
    
    def __init__(self, model_path: str):
        """Initialize the fastText model resource.
        
        Args:
            model_path: Absolute path to the fastText .ftz model file
        """
        self._model_path = model_path
        self._model = None
    
    @property
    def model(self):
        """Lazy-load and return the fastText model.
        
        Returns:
            fasttext model instance
            
        Raises:
            ImportError: if fasttext package is not installed
            FileNotFoundError: if model file doesn't exist
        """
        if self._model is None:
            try:
                import fasttext
            except ImportError as e:
                raise ImportError(
                    "fasttext package is required for language detection. "
                    "Install it with: poetry add fasttext"
                ) from e
            
            if not os.path.exists(self._model_path):
                raise FileNotFoundError(
                    f"FastText model not found at: {self._model_path}. "
                    f"Expected lid.176.ftz model file."
                )
            
            # Suppress fastText warnings during model loading
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._model = fasttext.load_model(self._model_path)
        
        return self._model
    
    def predict(self, text: str, k: int = 1):
        """Predict language(s) for given text.
        
        Args:
            text: Input text to detect language from
            k: Number of top predictions to return
            
        Returns:
            Tuple of (labels, probabilities)
        """
        return self.model.predict(text, k=k)


@resource(config_schema={"model_path": str})
def fasttext_model_resource(context: InitResourceContext) -> FastTextModelResource:
    """Dagster resource providing a fastText language detection model.
    
    Configuration:
        model_path (str): Path to the fastText .ftz model file
        
    Example:
        In your Dagster definitions:
        
        ```python
        from dagster import Definitions
        from src.pipeline.resources.fasttext_resource import fasttext_model_resource
        
        defs = Definitions(
            assets=[...],
            resources={
                "fasttext_model": fasttext_model_resource.configured({
                    "model_path": "/app/models/lid.176.ftz"
                })
            }
        )
        ```
        
        In your asset:
        
        ```python
        @asset(required_resource_keys={"fasttext_model"})
        def my_asset(context):
            model = context.resources.fasttext_model
            labels, probs = model.predict("Hello world", k=3)
        ```
    """
    model_path = context.resource_config["model_path"]
    context.log.info(f"Initializing FastText model resource from: {model_path}")
    
    resource = FastTextModelResource(model_path)
    
    # Warm up the model (trigger lazy loading) to catch errors early
    try:
        _ = resource.model
        context.log.info("FastText model loaded successfully")
    except Exception as e:
        context.log.error(f"Failed to load FastText model: {e}")
        raise
    
    return resource
