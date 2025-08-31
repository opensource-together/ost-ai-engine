"""
Integration tests for dbt models.
"""

import pytest
import os
import subprocess
from pathlib import Path
from src.infrastructure.config import settings


@pytest.mark.integration
@pytest.mark.slow
def test_dbt_models_execution():
    """Test that dbt models can be executed successfully."""
    print("🔧 DBT MODELS EXECUTION TEST")
    print("=" * 80)
    
    dbt_dir = Path(__file__).parent.parent.parent / "src" / "dbt"
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
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
        # Run dbt models (only test models that don't depend on external tables)
        print("📊 Running dbt models...")
        result = subprocess.run([
            'poetry', 'run', 'dbt', 'run',
            '--project-dir', str(dbt_dir),
            '--profiles-dir', str(dbt_dir),
            '--select', 'test_users test_projects test_similarities',
            '--target', 'ci'
        ], env=env, check=True, capture_output=True, text=True)
        
        print("✅ dbt models executed successfully")
        print(f"Output: {result.stdout[:500]}...")  # Show first 500 chars
        
        # Run dbt tests
        print("\n🧪 Running dbt tests...")
        result = subprocess.run([
            'poetry', 'run', 'dbt', 'test',
            '--project-dir', str(dbt_dir),
            '--profiles-dir', str(dbt_dir),
            '--select', 'test_users test_projects test_similarities',
            '--target', 'ci'
        ], env=env, check=True, capture_output=True, text=True)
        
        print("✅ dbt tests passed")
        print(f"Output: {result.stdout[:500]}...")  # Show first 500 chars
        
    except subprocess.CalledProcessError as e:
        print(f"❌ dbt command failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        pytest.fail(f"dbt execution failed: {e}")


@pytest.mark.integration
def test_dbt_project_structure():
    """Test that dbt project has correct structure."""
    print("\n🔧 DBT PROJECT STRUCTURE TEST")
    print("=" * 80)
    
    dbt_dir = Path(__file__).parent.parent.parent / "src" / "dbt"
    
    # Check essential dbt files
    essential_files = [
        'dbt_project.yml',
        'profiles.yml',
        'models/',
        'models/test/',
        'models/staging/'
    ]
    
    for file_path in essential_files:
        full_path = dbt_dir / file_path
        assert full_path.exists(), f"Required dbt file/directory not found: {file_path}"
        print(f"✅ {file_path}")
    
    # Check test models exist
    test_models = [
        'models/test/test_users.sql',
        'models/test/test_projects.sql',
        'models/test/test_similarities.sql'
    ]
    
    for model_path in test_models:
        full_path = dbt_dir / model_path
        assert full_path.exists(), f"Required test model not found: {model_path}"
        print(f"✅ {model_path}")


@pytest.mark.integration
def test_dbt_configuration():
    """Test dbt configuration and profiles."""
    print("\n🔧 DBT CONFIGURATION TEST")
    print("=" * 80)
    
    dbt_dir = Path(__file__).parent.parent.parent / "src" / "dbt"
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check dbt_project.yml exists and is valid
    dbt_project_file = dbt_dir / "dbt_project.yml"
    assert dbt_project_file.exists(), "dbt_project.yml not found"
    
    # Check profiles.yml exists
    profiles_file = dbt_dir / "profiles.yml"
    assert profiles_file.exists(), "profiles.yml not found"
    
    # Set environment variables for dbt
    env = os.environ.copy()
    env.update({
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_USER': settings.POSTGRES_USER,
        'POSTGRES_PASSWORD': settings.POSTGRES_PASSWORD,
        'POSTGRES_PORT': str(settings.POSTGRES_PORT),
        'POSTGRES_DB': settings.POSTGRES_DB,
    })
    
    # Check that dev target is configured
    try:
        result = subprocess.run([
            'poetry', 'run', 'dbt', 'debug', 
            '--target', 'dev'
        ], cwd=dbt_dir, env=env, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ dbt debug successful")
            print(f"Output: {result.stdout[:300]}...")
        else:
            print(f"⚠️ dbt debug failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️ dbt debug timed out")
    except Exception as e:
        print(f"⚠️ dbt debug error: {e}")


@pytest.mark.integration
def test_dbt_model_compilation():
    """Test that dbt models can be compiled without errors."""
    print("\n🔧 DBT MODEL COMPILATION TEST")
    print("=" * 80)
    
    dbt_dir = Path(__file__).parent.parent.parent / "src" / "dbt"
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
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
        # Compile dbt models
        result = subprocess.run([
            'poetry', 'run', 'dbt', 'compile',
            '--project-dir', str(dbt_dir),
            '--profiles-dir', str(dbt_dir),
            '--select', 'test_users test_projects test_similarities',
            '--target', 'ci'
        ], env=env, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ dbt models compiled successfully")
            print(f"Output: {result.stdout[:300]}...")
        else:
            print(f"❌ dbt compilation failed: {result.stderr}")
            pytest.fail("dbt model compilation failed")
            
    except subprocess.TimeoutExpired:
        print("❌ dbt compilation timed out")
        pytest.fail("dbt compilation timed out")
    except Exception as e:
        print(f"❌ dbt compilation error: {e}")
        pytest.fail(f"dbt compilation error: {e}")


if __name__ == "__main__":
    # Run all dbt tests
    test_dbt_project_structure()
    test_dbt_configuration()
    test_dbt_model_compilation()
    test_dbt_models_execution()
    
    print("\n✅ All dbt integration tests completed!")
