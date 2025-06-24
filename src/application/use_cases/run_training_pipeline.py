from src.application.services.project_data_loader import ProjectDataLoadingService
from src.infrastructure.analysis.feature_engineer import FeatureEngineer
from src.infrastructure.analysis.similarity_calculator import SimilarityCalculator
from src.infrastructure.analysis.model_persistence_service import ModelPersistenceService


def run_training_pipeline():
    """
    Executes the full model training pipeline.
    """
    print("Starting the model training pipeline...")

    # 1. Load data from the database
    print("Step 1: Loading project data...")
    loader = ProjectDataLoadingService()
    projects = loader.get_all_projects()

    if not projects:
        print("No projects found in the database. Aborting training.")
        return

    # 2. Engineer features
    print("Step 2: Engineering features...")
    feature_engineer = FeatureEngineer()
    feature_matrix, tfidf_vec, mlb, scaler = feature_engineer.fit_transform(projects)

    # 3. Calculate similarity
    print("Step 3: Calculating similarity matrix...")
    calculator = SimilarityCalculator()
    similarity_matrix = calculator.calculate(feature_matrix)

    # 4. Save model artifacts
    print("Step 4: Saving model artifacts...")
    persistence_service = ModelPersistenceService()
    artifacts = {
        "projects": projects,
        "similarity_matrix": similarity_matrix,
        "tfidf_vectorizer": tfidf_vec,
        "mlb_encoder": mlb,
        "scaler": scaler,
    }
    persistence_service.save_model_artifacts(artifacts)

    print("Model training pipeline completed successfully!")


if __name__ == "__main__":
    # This allows the script to be run directly for testing or manual triggers.
    run_training_pipeline() 