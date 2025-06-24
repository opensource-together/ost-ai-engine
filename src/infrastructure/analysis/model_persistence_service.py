import joblib
import os
from scipy.sparse import spmatrix


class ModelPersistenceService:
    """
    Handles saving and loading of model artifacts.
    """

    def __init__(self):
        """
        Initializes the service with a directory to store models,
        configured via the MODEL_DIR environment variable.
        """
        self.model_dir = os.getenv("MODEL_DIR", "models/")
        os.makedirs(self.model_dir, exist_ok=True)

    def save_model_artifacts(self, artifacts: dict):
        """
        Saves all trained model artifacts to the specified directory.

        Args:
            artifacts (dict): A dictionary where keys are filenames (e.g., 'similarity_matrix')
                              and values are the objects to save.
        """
        for name, artifact in artifacts.items():
            path = os.path.join(self.model_dir, f"{name}.pkl")
            joblib.dump(artifact, path)
        print(f"Model artifacts saved to {self.model_dir}")

    def load_model_artifacts(self) -> dict:
        """
        Loads all model artifacts from the specified directory.

        Returns:
            dict: A dictionary containing the loaded model artifacts.
        """
        artifacts = {}
        for filename in os.listdir(self.model_dir):
            if filename.endswith(".pkl"):
                name = filename.replace(".pkl", "")
                path = os.path.join(self.model_dir, filename)
                artifacts[name] = joblib.load(path)
        print(f"Model artifacts loaded from {self.model_dir}")
        return artifacts 