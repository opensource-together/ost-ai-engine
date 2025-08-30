import pytest
import subprocess
import os
from sqlalchemy import create_engine, text
from src.infrastructure.config import settings
import sys


@pytest.fixture(scope="session")
def setup_test_database():
    """Setup test database with minimal schema and test data using dbt."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create extensions
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()
    
    # Run dbt models for test data
    dbt_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'dbt')
    
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
        subprocess.run([
            'poetry', 'run', 'dbt', 'run', 
            '--select', 'tag:test', 
            '--target', 'ci'
        ], cwd=dbt_dir, env=env, check=True)
        print("✅ dbt models run successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  dbt run failed: {e}")
        print("Using fallback method...")
        
        # Use fallback script
        fallback_script = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'setup_test_data_fallback.py')
        try:
            subprocess.run([
                sys.executable, fallback_script
            ], check=True)
            print("✅ Fallback method completed successfully")
        except subprocess.CalledProcessError as fallback_error:
            print(f"❌ Fallback method also failed: {fallback_error}")
            print("Continuing with tests anyway...")
    
    yield engine
    
    # Cleanup (optional - database is destroyed anyway)
    with engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS "test_similarities" CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS "test_projects" CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS "test_users" CASCADE'))
        conn.commit()


@pytest.fixture
def db_connection(setup_test_database):
    """Provide database connection for tests."""
    engine = setup_test_database
    with engine.connect() as conn:
        yield conn


# Markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
