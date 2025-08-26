"""
MLflow service for model tracking and experiment management.
Replaces and extends ModelPersistenceService with MLflow capabilities.
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

import mlflow
import numpy as np
from dagster import get_dagster_logger

from src.infrastructure.config import settings


class MLflowService:
    """
    MLflow service for tracking ML experiments and model artifacts.
    Provides versioning, experiment tracking, and model comparison capabilities.
    """

    def __init__(self, tracking_uri: Optional[str] = None, experiment_name: str = "ost-data-engine"):
        """
        Initialize MLflow service.
        
        Args:
            tracking_uri: MLflow tracking URI (default: local SQLite)
            experiment_name: Name of the experiment
        """
        self.tracking_uri = tracking_uri or "sqlite:///mlflow.db"
        self.experiment_name = experiment_name
        self.logger = get_dagster_logger()
        
        # Set tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Get or create experiment
        self.experiment = mlflow.get_experiment_by_name(experiment_name)
        if self.experiment is None:
            self.experiment_id = mlflow.create_experiment(experiment_name)
            self.logger.info(f"✅ Created new MLflow experiment: {experiment_name}")
        else:
            self.experiment_id = self.experiment.experiment_id
            self.logger.info(f"✅ Using existing MLflow experiment: {experiment_name}")
        
        # Set experiment
        mlflow.set_experiment(experiment_name)

    def log_embedding_experiment(
        self,
        run_name: str,
        artifacts: Dict[str, Any],
        metadata: Dict[str, Any],
        model_name: str = "all-MiniLM-L6-v2"
    ) -> str:
        """
        Log an embedding generation experiment.
        
        Args:
            run_name: Name of the run
            artifacts: Dictionary containing model artifacts
            metadata: Additional metadata to log
            model_name: Name of the embedding model used
            
        Returns:
            str: Run ID
        """
        start_time = time.time()
        
        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            mlflow.log_params({
                "model_name": model_name,
                "embedding_dimensions": metadata.get("dimensions", 384),
                "batch_size": metadata.get("batch_size", 32),
                "projects_count": metadata.get("count", 0),
            })
            
            # Log metrics
            mlflow.log_metrics({
                "generation_time_seconds": metadata.get("generation_time", 0),
                "projects_processed": metadata.get("count", 0),
                "embedding_dimensions": metadata.get("dimensions", 384),
            })
            
            # Log artifacts (corrigé: pas de slash final)
            if "project_embeddings" in artifacts:
                np.save("temp_project_embeddings.npy", artifacts["project_embeddings"])
                mlflow.log_artifact("temp_project_embeddings.npy", "embeddings")
                os.remove("temp_project_embeddings.npy")
            
            if "user_embeddings" in artifacts:
                np.save("temp_user_embeddings.npy", artifacts["user_embeddings"])
                mlflow.log_artifact("temp_user_embeddings.npy", "embeddings")
                os.remove("temp_user_embeddings.npy")
            
            # Log metadata as artifact
            import json
            with open("temp_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            mlflow.log_artifact("temp_metadata.json", "metadata")
            os.remove("temp_metadata.json")
            
            # Log tags
            mlflow.set_tags({
                "experiment_type": "embedding_generation",
                "model_family": "sentence_transformers",
                "data_source": "github_projects",
            })
            
            run_id = run.info.run_id
            self.logger.info(f"✅ MLflow experiment logged: {run_name} (ID: {run_id})")
            
        return run_id

    def log_hybrid_embedding_experiment(
        self,
        run_name: str,
        metadata: Dict[str, Any],
        weights: Dict[str, float]
    ) -> str:
        """
        Log a hybrid embedding experiment.
        
        Args:
            run_name: Name of the run
            metadata: Experiment metadata
            weights: Similarity weights used
            
        Returns:
            str: Run ID
        """
        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            mlflow.log_params({
                "semantic_dimensions": metadata.get("semantic_dimensions", 384),
                "structured_dimensions": metadata.get("structured_dimensions", 38),
                "hybrid_dimensions": metadata.get("hybrid_dimensions", 422),
                **weights  # Log similarity weights as parameters
            })
            
            # Log metrics
            mlflow.log_metrics({
                "generation_time_seconds": metadata.get("generation_time", 0),
                "projects_processed": metadata.get("count", 0),
                "semantic_weight": weights.get("semantic", 0.1),
                "tech_stacks_weight": weights.get("tech_stacks", 0.6),
                "categories_weight": weights.get("categories", 0.3),
            })
            
            # Log weights as artifact (corrigé: pas de slash final)
            import json
            with open("temp_weights.json", "w") as f:
                json.dump(weights, f, indent=2)
            mlflow.log_artifact("temp_weights.json", "weights")
            os.remove("temp_weights.json")
            
            # Log tags
            mlflow.set_tags({
                "experiment_type": "hybrid_embedding",
                "model_family": "hybrid_semantic_structured",
                "data_source": "github_projects",
            })
            
            run_id = run.info.run_id
            self.logger.info(f"✅ MLflow hybrid experiment logged: {run_name} (ID: {run_id})")
            
        return run_id

    def get_best_run(self, metric: str = "projects_processed", order: str = "DESC") -> Optional[Dict[str, Any]]:
        """
        Get the best run based on a metric.
        
        Args:
            metric: Metric to optimize for
            order: Sort order (ASC or DESC)
            
        Returns:
            Dict containing run information or None
        """
        try:
            runs = mlflow.search_runs(
                experiment_ids=[self.experiment_id],
                order_by=[f"metrics.{metric} {order}"]
            )
            
            if runs.empty:
                self.logger.warning("⚠️ No runs found in experiment")
                return None
            
            best_run = runs.iloc[0]
            return {
                "run_id": best_run["run_id"],
                "run_name": best_run["tags.mlflow.runName"],
                "metric_value": best_run[f"metrics.{metric}"],
                "status": best_run["status"],
                "start_time": best_run["start_time"],
            }
        except Exception as e:
            self.logger.error(f"❌ Error getting best run: {e}")
            return None

    def compare_runs(self, run_ids: list[str]) -> Dict[str, Any]:
        """
        Compare multiple runs.
        
        Args:
            run_ids: List of run IDs to compare
            
        Returns:
            Dictionary with comparison data
        """
        try:
            runs = mlflow.search_runs(
                experiment_ids=[self.experiment_id],
                filter_string=f"run_id IN ({','.join(run_ids)})"
            )
            
            comparison = {}
            for _, run in runs.iterrows():
                run_id = run["run_id"]
                comparison[run_id] = {
                    "run_name": run["tags.mlflow.runName"],
                    "metrics": {
                        "generation_time_seconds": run.get("metrics.generation_time_seconds", 0),
                        "projects_processed": run.get("metrics.projects_processed", 0),
                        "embedding_dimensions": run.get("metrics.embedding_dimensions", 384),
                    },
                    "params": {
                        "model_name": run.get("params.model_name", "unknown"),
                        "batch_size": run.get("params.batch_size", 32),
                    },
                    "status": run["status"],
                }
            
            self.logger.info(f"✅ Compared {len(run_ids)} runs")
            return comparison
            
        except Exception as e:
            self.logger.error(f"❌ Error comparing runs: {e}")
            return {}

    def list_experiments(self) -> list[Dict[str, Any]]:
        """
        List all experiments.
        
        Returns:
            List of experiment information
        """
        try:
            experiments = mlflow.search_experiments()
            return [
                {
                    "experiment_id": exp.experiment_id,
                    "name": exp.name,
                    "artifact_location": exp.artifact_location,
                    "lifecycle_stage": exp.lifecycle_stage,
                }
                for exp in experiments
            ]
        except Exception as e:
            self.logger.error(f"❌ Error listing experiments: {e}")
            return []

    def cleanup_old_runs(self, days_old: int = 30) -> int:
        """
        Clean up old runs to save space.
        
        Args:
            days_old: Delete runs older than this many days
            
        Returns:
            Number of runs deleted
        """
        try:
            import datetime
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
            
            runs = mlflow.search_runs(
                experiment_ids=[self.experiment_id],
                filter_string=f"start_time < '{cutoff_date.isoformat()}'"
            )
            
            deleted_count = 0
            for _, run in runs.iterrows():
                try:
                    mlflow.delete_run(run["run_id"])
                    deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not delete run {run['run_id']}: {e}")
            
            self.logger.info(f"✅ Cleaned up {deleted_count} old runs")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up runs: {e}")
            return 0


# Global instance for easy access
mlflow_service = MLflowService()
