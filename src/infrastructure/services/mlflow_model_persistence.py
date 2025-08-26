"""
MLflow service for model persistence only.
Replaces ModelPersistenceService with MLflow model registry capabilities.
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

import mlflow
import numpy as np
from dagster import get_dagster_logger

from src.infrastructure.config import settings


class MLflowModelPersistence:
    """
    MLflow service for model persistence and versioning.
    Focuses only on saving/loading models, not experiment tracking.
    """

    def __init__(self, tracking_uri: Optional[str] = None, model_registry_name: Optional[str] = None):
        """
        Initialize MLflow model persistence service.
        
        Args:
            tracking_uri: MLflow tracking URI (default from settings)
            model_registry_name: Name for the model registry (default from settings)
        """
        self.tracking_uri = tracking_uri or settings.MLFLOW_TRACKING_URI
        self.model_registry_name = model_registry_name or settings.MLFLOW_MODEL_REGISTRY_NAME
        self.logger = get_dagster_logger()
        
        # Set tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Create or get model registry
        try:
            self.client = mlflow.tracking.MlflowClient()
            # Model registry will be created automatically when first model is registered
        except Exception as e:
            self.logger.warning(f"⚠️ Could not initialize MLflow client: {e}")

    def save_model_artifacts(self, artifacts: Dict[str, Any], model_name: str = "embeddings_model") -> str:
        """
        Save model artifacts using MLflow model registry.
        
        Args:
            artifacts: Dictionary containing model artifacts
            model_name: Name for the model
            
        Returns:
            str: Model version URI
        """
        try:
            # Create a temporary directory for artifacts
            temp_dir = f"temp_{model_name}_{int(time.time())}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save artifacts to temp directory
            for name, artifact in artifacts.items():
                if isinstance(artifact, np.ndarray):
                    np.save(os.path.join(temp_dir, f"{name}.npy"), artifact)
                else:
                    import pickle
                    with open(os.path.join(temp_dir, f"{name}.pkl"), "wb") as f:
                        pickle.dump(artifact, f)
            
            # Log model with MLflow
            with mlflow.start_run(run_name=f"{model_name}_persistence"):
                # Log artifacts
                mlflow.log_artifacts(temp_dir, "model_artifacts")
                
                # Log model metadata
                metadata = {
                    "model_name": model_name,
                    "artifact_count": len(artifacts),
                    "artifact_names": list(artifacts.keys()),
                    "saved_at": time.time(),
                }
                
                import json
                with open(os.path.join(temp_dir, "metadata.json"), "w") as f:
                    json.dump(metadata, f, indent=2)
                mlflow.log_artifact(os.path.join(temp_dir, "metadata.json"), "metadata")
                
                # Register model
                model_uri = f"runs:/{mlflow.active_run().info.run_id}/model_artifacts"
                
                # Register in model registry
                try:
                    # First, create the registered model if it doesn't exist
                    try:
                        self.client.create_registered_model(name=model_name)
                        self.logger.info(f"✅ Created registered model: {model_name}")
                    except Exception:
                        # Model already exists, that's fine
                        pass
                    
                    # Now create the model version
                    mv = self.client.create_model_version(
                        name=model_name,
                        source=model_uri,
                        run_id=mlflow.active_run().info.run_id
                    )
                    model_version_uri = f"models:/{model_name}/{mv.version}"
                    self.logger.info(f"✅ Model registered: {model_name} v{mv.version}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not register model in registry: {e}")
                    model_version_uri = model_uri
            
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir)
            
            return model_version_uri
            
        except Exception as e:
            self.logger.error(f"❌ Error saving model artifacts: {e}")
            raise

    def save_embeddings(self, name: str, artifacts: Dict[str, Any]) -> str:
        """
        Save embeddings using MLflow (replaces ModelPersistenceService.save_embeddings).
        
        Args:
            name: Base name for the model
            artifacts: Dictionary containing embeddings and metadata
            
        Returns:
            str: Model version URI
        """
        model_name = f"{name}_embeddings"
        return self.save_model_artifacts(artifacts, model_name)

    def load_model_artifacts(self, model_name: str = "embeddings_model", version: Optional[int] = None) -> Dict[str, Any]:
        """
        Load model artifacts from MLflow model registry.
        
        Args:
            model_name: Name of the model to load
            version: Specific version to load (None = latest)
            
        Returns:
            dict: Loaded model artifacts
        """
        try:
            # Get model version
            if version is None:
                # Get latest version
                model_versions = self.client.search_model_versions(f"name='{model_name}'")
                if not model_versions:
                    raise Exception(f"No model versions found for {model_name}")
                latest_version = max(model_versions, key=lambda x: x.version)
                model_uri = f"models:/{model_name}/{latest_version.version}"
            else:
                model_uri = f"models:/{model_name}/{version}"
            
            # Download artifacts
            temp_dir = f"temp_load_{model_name}_{int(time.time())}"
            mlflow.artifacts.download_artifacts(artifact_uri=model_uri, dst_path=temp_dir)
            
            # Load artifacts
            artifacts = {}
            artifacts_dir = os.path.join(temp_dir, "model_artifacts")
            
            if os.path.exists(artifacts_dir):
                for filename in os.listdir(artifacts_dir):
                    file_path = os.path.join(artifacts_dir, filename)
                    name, ext = os.path.splitext(filename)
                    
                    if ext == ".npy":
                        artifacts[name] = np.load(file_path)
                    elif ext == ".pkl":
                        import pickle
                        with open(file_path, "rb") as f:
                            artifacts[name] = pickle.load(f)
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            self.logger.info(f"✅ Loaded model artifacts from {model_uri}")
            return artifacts
            
        except Exception as e:
            self.logger.error(f"❌ Error loading model artifacts: {e}")
            raise

    def list_models(self) -> list[Dict[str, Any]]:
        """
        List all registered models.
        
        Returns:
            List of model information
        """
        try:
            models = self.client.list_registered_models()
            return [
                {
                    "name": model.name,
                    "creation_timestamp": model.creation_timestamp,
                    "last_updated_timestamp": model.last_updated_timestamp,
                    "description": model.description,
                }
                for model in models
            ]
        except Exception as e:
            self.logger.error(f"❌ Error listing models: {e}")
            return []

    def list_model_versions(self, model_name: str) -> list[Dict[str, Any]]:
        """
        List all versions of a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of version information
        """
        try:
            versions = self.client.search_model_versions(f"name='{model_name}'")
            return [
                {
                    "version": version.version,
                    "run_id": version.run_id,
                    "status": version.status,
                    "creation_timestamp": version.creation_timestamp,
                }
                for version in versions
            ]
        except Exception as e:
            self.logger.error(f"❌ Error listing model versions: {e}")
            return []

    def delete_model_version(self, model_name: str, version: int) -> bool:
        """
        Delete a specific model version.
        
        Args:
            model_name: Name of the model
            version: Version to delete
            
        Returns:
            bool: Success status
        """
        try:
            self.client.delete_model_version(name=model_name, version=version)
            self.logger.info(f"✅ Deleted model version: {model_name} v{version}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error deleting model version: {e}")
            return False


# Global instance for easy access
mlflow_model_persistence = MLflowModelPersistence()
