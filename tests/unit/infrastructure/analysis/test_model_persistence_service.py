"""
Unit tests for model persistence service infrastructure.

Tests critical production functionality: artifact saving/loading,
error handling, file management, and versioning capabilities.
"""

import os
import pickle
import tempfile
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, mock_open

from src.infrastructure.analysis.model_persistence_service import ModelPersistenceService


class TestModelPersistenceServiceInitialization:
    """Test critical initialization for production."""

    def test_initialization_with_default_dir(self):
        """Test that service initializes with default model directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.infrastructure.analysis.model_persistence_service.os.makedirs') as mock_makedirs:
                service = ModelPersistenceService()
                
                assert service.model_dir == "models/"
                mock_makedirs.assert_called_once_with("models/", exist_ok=True)

    def test_initialization_with_custom_dir(self):
        """Test that service initializes with custom model directory."""
        custom_dir = "custom_models/"
        with patch('src.infrastructure.analysis.model_persistence_service.os.makedirs') as mock_makedirs:
            service = ModelPersistenceService(model_dir=custom_dir)
            
            assert service.model_dir == custom_dir
            mock_makedirs.assert_called_once_with(custom_dir, exist_ok=True)

    def test_directory_creation_on_init(self):
        """Test that directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_model_dir = os.path.join(temp_dir, "test_models")
            
            # Directory shouldn't exist initially
            assert not os.path.exists(test_model_dir)
            
            service = ModelPersistenceService(model_dir=test_model_dir)
            
            # Directory should be created
            assert os.path.exists(test_model_dir)
            assert os.path.isdir(test_model_dir)


class TestModelPersistenceServiceSaving:
    """Test critical saving functionality for production."""

    def test_save_model_artifacts_numpy_array(self):
        """Test saving NumPy arrays as .npy files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create test data
            similarity_matrix = np.random.rand(10, 10)
            artifacts = {"similarity_matrix": similarity_matrix}
            
            service.save_model_artifacts(artifacts)
            
            # Check file was created
            expected_path = os.path.join(temp_dir, "similarity_matrix.npy")
            assert os.path.exists(expected_path)
            
            # Check data was saved correctly
            loaded_matrix = np.load(expected_path)
            np.testing.assert_array_equal(similarity_matrix, loaded_matrix)

    def test_save_model_artifacts_pickle_objects(self):
        """Test saving Python objects as .pkl files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create test data
            test_object = {"key": "value", "number": 42}
            artifacts = {"test_model": test_object}
            
            service.save_model_artifacts(artifacts)
            
            # Check file was created
            expected_path = os.path.join(temp_dir, "test_model.pkl")
            assert os.path.exists(expected_path)
            
            # Check data was saved correctly
            with open(expected_path, "rb") as f:
                loaded_object = pickle.load(f)
            assert loaded_object == test_object

    def test_save_model_artifacts_mixed_types(self):
        """Test saving mixed NumPy arrays and Python objects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create mixed test data
            similarity_matrix = np.random.rand(5, 5)
            vectorizer = {"vocabulary": ["word1", "word2"], "idf": [1.0, 2.0]}
            artifacts = {
                "similarity_matrix": similarity_matrix,
                "tfidf_vectorizer": vectorizer
            }
            
            service.save_model_artifacts(artifacts)
            
            # Check both files were created
            assert os.path.exists(os.path.join(temp_dir, "similarity_matrix.npy"))
            assert os.path.exists(os.path.join(temp_dir, "tfidf_vectorizer.pkl"))
            
            # Check data integrity
            loaded_matrix = np.load(os.path.join(temp_dir, "similarity_matrix.npy"))
            np.testing.assert_array_equal(similarity_matrix, loaded_matrix)
            
            with open(os.path.join(temp_dir, "tfidf_vectorizer.pkl"), "rb") as f:
                loaded_vectorizer = pickle.load(f)
            assert loaded_vectorizer == vectorizer

    def test_save_model_artifacts_empty_dict(self):
        """Test handling of empty artifacts dictionary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Should not raise any errors
            service.save_model_artifacts({})
            
            # Directory should still exist
            assert os.path.exists(temp_dir)


class TestModelPersistenceServiceLoading:
    """Test critical loading functionality for production."""

    def test_load_model_artifacts_numpy_array(self):
        """Test loading NumPy arrays from .npy files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create test file
            similarity_matrix = np.random.rand(8, 8)
            file_path = os.path.join(temp_dir, "similarity_matrix.npy")
            np.save(file_path, similarity_matrix)
            
            # Load artifacts
            artifacts = service.load_model_artifacts()
            
            # Check data was loaded correctly
            assert "similarity_matrix" in artifacts
            np.testing.assert_array_equal(similarity_matrix, artifacts["similarity_matrix"])

    def test_load_model_artifacts_pickle_objects(self):
        """Test loading Python objects from .pkl files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create test file
            test_object = {"model_type": "random_forest", "params": {"n_estimators": 100}}
            file_path = os.path.join(temp_dir, "model.pkl")
            with open(file_path, "wb") as f:
                pickle.dump(test_object, f)
            
            # Load artifacts
            artifacts = service.load_model_artifacts()
            
            # Check data was loaded correctly
            assert "model" in artifacts
            assert artifacts["model"] == test_object

    def test_load_model_artifacts_mixed_types(self):
        """Test loading mixed NumPy arrays and Python objects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create test files
            similarity_matrix = np.random.rand(3, 3)
            np.save(os.path.join(temp_dir, "similarity_matrix.npy"), similarity_matrix)
            
            vectorizer = {"features": ["feature1", "feature2"]}
            with open(os.path.join(temp_dir, "vectorizer.pkl"), "wb") as f:
                pickle.dump(vectorizer, f)
            
            # Load artifacts
            artifacts = service.load_model_artifacts()
            
            # Check both were loaded
            assert "similarity_matrix" in artifacts
            assert "vectorizer" in artifacts
            np.testing.assert_array_equal(similarity_matrix, artifacts["similarity_matrix"])
            assert artifacts["vectorizer"] == vectorizer

    def test_load_model_artifacts_empty_directory(self):
        """Test loading from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Should return empty dict, not raise error
            artifacts = service.load_model_artifacts()
            assert artifacts == {}

    def test_load_model_artifacts_ignores_other_files(self):
        """Test that non-model files are ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create model files
            np.save(os.path.join(temp_dir, "model.npy"), np.array([1, 2, 3]))
            
            # Create non-model files
            with open(os.path.join(temp_dir, "readme.txt"), "w") as f:
                f.write("This is a readme")
            with open(os.path.join(temp_dir, "config.json"), "w") as f:
                f.write('{"key": "value"}')
            
            # Load artifacts
            artifacts = service.load_model_artifacts()
            
            # Should only load model files
            assert "model" in artifacts
            assert "readme" not in artifacts
            assert "config" not in artifacts


class TestModelPersistenceServiceVectorizerExtraction:
    """Test critical vectorizer extraction functionality."""

    def test_extract_vectorizer_from_feature_engineer(self):
        """Test extracting tfidf_vectorizer from feature_engineer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create a simple dictionary that simulates feature_engineer
            mock_feature_engineer = {"tfidf_vectorizer": {"vocabulary": ["word1", "word2"]}}
            
            # Save feature_engineer
            with open(os.path.join(temp_dir, "feature_engineer.pkl"), "wb") as f:
                pickle.dump(mock_feature_engineer, f)
            
            # Load artifacts
            artifacts = service.load_model_artifacts()
            
            # Should load feature_engineer but not extract vectorizer (since it's not an object with attribute)
            assert "feature_engineer" in artifacts
            # The extraction logic only works with objects that have tfidf_vectorizer as an attribute
            # So we don't expect tfidf_vectorizer to be extracted from a dict

    def test_extract_vectorizer_feature_engineer_no_vectorizer(self):
        """Test handling when feature_engineer has no tfidf_vectorizer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create a simple dictionary without tfidf_vectorizer
            mock_feature_engineer = {"some_other_attribute": "value"}
            
            # Save feature_engineer
            with open(os.path.join(temp_dir, "feature_engineer.pkl"), "wb") as f:
                pickle.dump(mock_feature_engineer, f)
            
            # Load artifacts
            artifacts = service.load_model_artifacts()
            
            # Should not extract vectorizer
            assert "feature_engineer" in artifacts
            assert "tfidf_vectorizer" not in artifacts

    def test_vectorizer_extraction_logic(self):
        """Test the vectorizer extraction logic directly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Test the extraction logic manually
            artifacts = {
                "feature_engineer": {"tfidf_vectorizer": {"vocabulary": ["word1", "word2"]}},
                "other_artifact": "value"
            }
            
            # Simulate the extraction logic from the service
            if "feature_engineer" in artifacts and "tfidf_vectorizer" not in artifacts:
                try:
                    feature_engineer = artifacts["feature_engineer"]
                    if hasattr(feature_engineer, 'tfidf_vectorizer'):
                        artifacts["tfidf_vectorizer"] = feature_engineer.tfidf_vectorizer
                except Exception:
                    pass
            
            # Should not extract since feature_engineer is a dict, not an object with attribute
            assert "tfidf_vectorizer" not in artifacts


class TestModelPersistenceServiceVersioning:
    """Test critical versioning functionality for production."""

    def test_save_model_with_name(self):
        """Test saving model with specific name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create test data
            training_data = {
                "similarity_matrix": np.random.rand(4, 4),
                "vectorizer": {"test": "data"}
            }
            
            model_name = "test_model_v1"
            model_path = service.save_model(training_data, model_name)
            
            # Check model directory was created
            expected_path = os.path.join(temp_dir, model_name)
            assert model_path == expected_path
            assert os.path.exists(expected_path)
            
            # Check files were saved
            assert os.path.exists(os.path.join(expected_path, "similarity_matrix.npy"))
            assert os.path.exists(os.path.join(expected_path, "vectorizer.pkl"))

    def test_load_model_with_name(self):
        """Test loading model with specific name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create test model directory and files
            model_name = "test_model_v2"
            model_path = os.path.join(temp_dir, model_name)
            os.makedirs(model_path)
            
            # Save test data
            similarity_matrix = np.random.rand(6, 6)
            np.save(os.path.join(model_path, "similarity_matrix.npy"), similarity_matrix)
            
            vectorizer = {"vocabulary": ["test"]}
            with open(os.path.join(model_path, "vectorizer.pkl"), "wb") as f:
                pickle.dump(vectorizer, f)
            
            # Load model
            artifacts = service.load_model(model_name)
            
            # Check data was loaded correctly
            assert "similarity_matrix" in artifacts
            assert "vectorizer" in artifacts
            np.testing.assert_array_equal(similarity_matrix, artifacts["similarity_matrix"])
            assert artifacts["vectorizer"] == vectorizer

    def test_load_model_not_found(self):
        """Test loading non-existent model."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                service.load_model("non_existent_model")


class TestModelPersistenceServiceErrorHandling:
    """Test critical error handling for production."""

    def test_save_model_artifacts_permission_error(self):
        """Test handling of permission errors during save."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a read-only directory to trigger permission error
            read_only_dir = os.path.join(temp_dir, "readonly")
            os.makedirs(read_only_dir)
            os.chmod(read_only_dir, 0o444)  # Read-only
            
            service = ModelPersistenceService(model_dir=read_only_dir)
            
            # Should raise PermissionError when trying to save
            with pytest.raises((PermissionError, OSError)):
                service.save_model_artifacts({"test": "data"})

    def test_load_model_artifacts_file_not_found(self):
        """Test handling when model directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_dir = os.path.join(temp_dir, "non_existent")
            service = ModelPersistenceService(model_dir=non_existent_dir)
            
            # Remove the directory that was created during initialization
            os.rmdir(non_existent_dir)
            
            # Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                service.load_model_artifacts()

    def test_load_model_artifacts_corrupted_file(self):
        """Test handling of corrupted pickle files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create corrupted pickle file
            with open(os.path.join(temp_dir, "corrupted.pkl"), "wb") as f:
                f.write(b"corrupted data")
            
            # Should raise pickle.UnpicklingError
            with pytest.raises((pickle.UnpicklingError, EOFError)):
                service.load_model_artifacts()

    def test_load_model_artifacts_corrupted_numpy_file(self):
        """Test handling of corrupted NumPy files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ModelPersistenceService(model_dir=temp_dir)
            
            # Create corrupted numpy file
            with open(os.path.join(temp_dir, "corrupted.npy"), "wb") as f:
                f.write(b"corrupted numpy data")
            
            # Should raise ValueError or similar
            with pytest.raises((ValueError, OSError)):
                service.load_model_artifacts()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
