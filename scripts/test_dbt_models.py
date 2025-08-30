#!/usr/bin/env python3
"""
Script to test dbt models locally.
This script runs the test models and validates the data.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config import settings


def run_dbt_models():
    """Run dbt test models."""
    print("🔧 Running dbt test models...")
    
    dbt_dir = project_root / "src" / "dbt"
    
    # Set environment variables for dbt
    env = os.environ.copy()
    env.update({
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_USER': settings.POSTGRES_USER,
        'POSTGRES_PASSWORD': settings.POSTGRES_PASSWORD,
        'POSTGRES_PORT': str(settings.POSTGRES_PORT),
        'POSTGRES_DB': settings.POSTGRES_DB,
    })
    
    try:
        # Run dbt models
        result = subprocess.run([
            'poetry', 'run', 'dbt', 'run', 
            '--select', 'tag:test', 
            '--target', 'dev'
        ], cwd=dbt_dir, env=env, check=True, capture_output=True, text=True)
        
        print("✅ dbt models run successfully")
        print(result.stdout)
        
        # Run dbt tests
        print("\n🧪 Running dbt tests...")
        result = subprocess.run([
            'poetry', 'run', 'dbt', 'test', 
            '--select', 'tag:test', 
            '--target', 'dev'
        ], cwd=dbt_dir, env=env, check=True, capture_output=True, text=True)
        
        print("✅ dbt tests passed")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ dbt command failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    run_dbt_models()
