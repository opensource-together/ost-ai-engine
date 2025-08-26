import os
import pickle

import numpy as np

from src.infrastructure.logger import log


class ModelPersistenceService:
    """
    Handles saving and loading of model artifacts.
    """

    def __init__(self, model_dir: str = "models/"):
        """
        Initializes the service with a directory to store models.

        Args:
            model_dir (str): The directory to save/load models from.
        """
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)

    def save_model_artifacts(self, artifacts: dict):
        """
        Saves all trained model artifacts to the specified directory.
        Handles NumPy arrays separately for efficiency.

        Args:
            artifacts (dict): A dictionary where keys are filenames
                              (e.g., 'similarity_matrix') and values are the
                              objects to save.
        """
        for name, artifact in artifacts.items():
            if name == "similarity_matrix":
                path = os.path.join(self.model_dir, f"{name}.npy")
                np.save(path, artifact)
            else:
                path = os.path.join(self.model_dir, f"{name}.pkl")
                with open(path, "wb") as f:
                    pickle.dump(artifact, f)

        log.info(f"Model artifacts saved to {self.model_dir}")

    def load_model_artifacts(self) -> dict:
        """
        Loads all model artifacts from the specified directory.
        Handles both .pkl and .npy files.
        Extracts tfidf_vectorizer from feature_engineer if needed.

        Returns:
            dict: A dictionary containing the loaded model artifacts.
        """
        artifacts = {}
        for filename in os.listdir(self.model_dir):
            name, ext = os.path.splitext(filename)
            path = os.path.join(self.model_dir, filename)

            if ext == ".npy":
                artifacts[name] = np.load(path)
            elif ext == ".pkl":
                with open(path, "rb") as f:
                    artifacts[name] = pickle.load(f)

        # Extract tfidf_vectorizer from feature_engineer if it exists
        if "feature_engineer" in artifacts and "tfidf_vectorizer" not in artifacts:
            try:
                feature_engineer = artifacts["feature_engineer"]
                if hasattr(feature_engineer, "tfidf_vectorizer"):
                    artifacts["tfidf_vectorizer"] = feature_engineer.tfidf_vectorizer
                    log.info("✅ Extracted tfidf_vectorizer from feature_engineer")
            except Exception as e:
                log.warning(f"⚠️ Could not extract vectorizer from feature_engineer: {e}")

        log.info(f"Model artifacts loaded from {self.model_dir}")
        return artifacts

    def save_model(self, training_data: dict, model_name: str) -> str:
        """
        Saves a trained model with a specific name.

        Args:
            training_data (dict): Dictionary containing model artifacts
            model_name (str): Name for the model version

        Returns:
            str: Path where the model was saved
        """
        model_path = os.path.join(self.model_dir, model_name)
        os.makedirs(model_path, exist_ok=True)

        # Save each artifact in the named model directory
        for name, artifact in training_data.items():
            if name == "similarity_matrix":
                path = os.path.join(model_path, f"{name}.npy")
                np.save(path, artifact)
            else:
                path = os.path.join(model_path, f"{name}.pkl")
                with open(path, "wb") as f:
                    pickle.dump(artifact, f)

        log.info(f"Model '{model_name}' saved to {model_path}")
        return model_path

    def load_model(self, model_name: str) -> dict:
        """
        Loads a specific model by name.

        Args:
            model_name (str): Name of the model to load

        Returns:
            dict: Dictionary containing the loaded model artifacts
        """
        model_path = os.path.join(self.model_dir, model_name)

        artifacts = {}
        for filename in os.listdir(model_path):
            name, ext = os.path.splitext(filename)
            path = os.path.join(model_path, filename)

            if ext == ".npy":
                artifacts[name] = np.load(path)
            elif ext == ".pkl":
                with open(path, "rb") as f:
                    artifacts[name] = pickle.load(f)

        log.info(f"Model '{model_name}' loaded from {model_path}")
        return artifacts

    # --- Added for Dagster assets compatibility ---
    def save_embeddings(self, name: str, artifacts: dict) -> None:
        """Save embedding artifacts in flat files (np and pkl) under models/.

        Args:
            name: base name for files (unused but kept for compatibility)
            artifacts: dict with numpy arrays and metadata to persist
        """
        # Save main array(s)
        if "project_embeddings" in artifacts:
            np.save(os.path.join(self.model_dir, "project_embeddings.npy"), artifacts["project_embeddings"]) 
        if "user_embeddings" in artifacts:
            np.save(os.path.join(self.model_dir, "user_embeddings.npy"), artifacts["user_embeddings"]) 

        # Save ids/metadata as pickle
        safe = {k: v for k, v in artifacts.items() if k not in {"project_embeddings", "user_embeddings"}}
        with open(os.path.join(self.model_dir, f"{name}_metadata.pkl"), "wb") as f:
            pickle.dump(safe, f)
        
        log.info(f"✅ Saved embeddings artifacts for {name} in {self.model_dir}")
