#!/usr/bin/env python3
"""
Script to start MLflow UI for experiment tracking.
"""

import subprocess
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.config import settings

def start_mlflow_ui():
    """Start MLflow UI server."""
    
    print("🚀 Starting MLflow UI...")
    print(f"📊 MLflow UI will be available at: http://localhost:{settings.MLFLOW_UI_PORT}")
    print(f"📁 Tracking URI: {settings.MLFLOW_TRACKING_URI}")
    print(f"📁 Artifact Root: {settings.MLFLOW_ARTIFACT_ROOT}")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
                # Start MLflow UI
        subprocess.run([
            "mlflow", "ui",
            "--host", settings.MLFLOW_UI_HOST,
            "--port", str(settings.MLFLOW_UI_PORT),
            "--backend-store-uri", settings.MLFLOW_TRACKING_URI,
            "--default-artifact-root", settings.MLFLOW_ARTIFACT_ROOT
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 MLflow UI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting MLflow UI: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ MLflow not found. Please install it with: pip install mlflow")
        sys.exit(1)

if __name__ == "__main__":
    start_mlflow_ui()
