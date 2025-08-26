#!/usr/bin/env python3
"""
Script to start MLflow UI for experiment tracking.
"""

import subprocess
import sys
import os
from pathlib import Path

def start_mlflow_ui():
    """Start MLflow UI server."""
    
    print("🚀 Starting MLflow UI...")
    print("📊 MLflow UI will be available at: http://localhost:505eans 0")
    print("📁 Tracking URI: sqlite:///mlflow.db")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start MLflow UI
        subprocess.run([
            "mlflow", "ui",
            "--host", "0.0.0.0",
            "--port", "5050",
            "--backend-store-uri", "sqlite:///mlflow.db",
            "--default-artifact-root", "./mlflow_artifacts"
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
