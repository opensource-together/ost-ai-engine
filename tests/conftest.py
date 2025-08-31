import pytest
import subprocess
import os
from sqlalchemy import create_engine, text
from src.infrastructure.config import settings
import sys
from unittest.mock import Mock, patch


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


# ============================================================================
# MOCK FIXTURES - Centralized test data and mocks
# ============================================================================

@pytest.fixture
def mock_settings():
    """Mock settings for unit tests."""
    return {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': 384,
        'GO_API_PORT': 8080,
        'REDIS_CACHE_URL': 'redis://localhost:6379/0',
        'RECOMMENDATION_TOP_N': 5,
        'RECOMMENDATION_MIN_SIMILARITY': 0.1,
        'RECOMMENDATION_SEMANTIC_WEIGHT': 0.25,
        'RECOMMENDATION_CATEGORY_WEIGHT': 0.45,
        'RECOMMENDATION_TECH_WEIGHT': 0.5,
        'RECOMMENDATION_POPULARITY_WEIGHT': 0.1,
        'RECOMMENDATION_MAX_PROJECTS': 1000,
        'RECOMMENDATION_POPULARITY_THRESHOLD': 100000,
        'LOG_LEVEL': 'INFO',
        'ENVIRONMENT': 'development'
    }


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        'user_id': '123e4567-e89b-12d3-a456-426614174000',
        'username': 'test_user',
        'bio': 'Python developer',
        'location': 'Paris',
        'company': 'Tech Corp',
        'embedding_vector': '{0.1,0.2,0.3,0.4,0.5}',
        'categories': ['Data Science', 'Machine Learning'],
        'tech_stacks': ['Python', 'TensorFlow']
    }


@pytest.fixture
def mock_user_profile():
    """Mock user profile for testing."""
    return {
        'user_id': '123e4567-e89b-12d3-a456-426614174000',
        'username': 'test_user',
        'bio': 'Python developer',
        'location': 'Paris',
        'company': 'Tech Corp',
        'embedding': [0.1, 0.2, 0.3, 0.4, 0.5],
        'categories': ['Data Science', 'Machine Learning'],
        'tech_stacks': ['Python', 'TensorFlow']
    }


@pytest.fixture
def mock_project_data():
    """Mock project data for testing."""
    return {
        'project_id': '123e4567-e89b-12d3-a456-426614174001',
        'title': 'Test Project',
        'description': 'A test project for ML',
        'primary_language': 'Python',
        'stargazers_count': 100,
        'embedding_vector': '{0.2,0.3,0.4,0.5,0.6}',
        'categories': ['Data Science'],
        'tech_stacks': ['Python', 'Scikit-learn']
    }


@pytest.fixture
def mock_similarity_data():
    """Mock similarity data for testing."""
    return {
        'user_id': '123e4567-e89b-12d3-a456-426614174000',
        'project_id': '123e4567-e89b-12d3-a456-426614174001',
        'similarity_score': 0.85,
        'semantic_score': 0.8,
        'category_score': 0.9,
        'tech_score': 0.7,
        'popularity_score': 0.6
    }


@pytest.fixture
def mock_db_connection():
    """Mock database connection for unit tests."""
    mock_conn = Mock()
    mock_result = Mock()
    mock_fetchone = Mock()
    
    # Mock user data
    mock_user_data = (
        "123e4567-e89b-12d3-a456-426614174000",  # user_id
        "test_user",                             # username
        "Python developer",                      # bio
        "Paris",                                 # location
        "Tech Corp",                             # company
        "{0.1,0.2,0.3,0.4,0.5}",               # embedding_vector
        ["Data Science", "Machine Learning"],    # categories
        ["Python", "TensorFlow"]                 # tech_stacks
    )
    
    mock_fetchone.return_value = mock_user_data
    mock_result.fetchone = mock_fetchone
    mock_conn.execute.return_value = mock_result
    
    return mock_conn


@pytest.fixture
def mock_redis_cache():
    """Mock Redis cache for testing."""
    cache_data = {}
    
    class MockRedisCache:
        def set(self, key, value, ttl=60, namespace=None):
            full_key = f"{namespace}:{key}" if namespace else key
            cache_data[full_key] = value
            return True
        
        def get(self, key, namespace=None):
            full_key = f"{namespace}:{key}" if namespace else key
            return cache_data.get(full_key)
        
        def clear(self):
            cache_data.clear()
    
    return MockRedisCache()


@pytest.fixture
def sample_vectors():
    """Sample vectors for testing."""
    return {
        'user_embedding': [0.1, 0.2, 0.3, 0.4, 0.5] * 76,  # 384 dimensions
        'project_embedding': [0.2, 0.3, 0.4, 0.5, 0.6] * 76,  # 384 dimensions
        'postgresql_format': '{0.1,0.2,0.3,0.4,0.5}',
        'json_format': '[0.1,0.2,0.3,0.4,0.5]',
        'invalid_format': 'invalid_vector_string'
    }


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture
def test_environment():
    """Set up test environment variables."""
    test_env = {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': '384',
        'GO_API_PORT': '8080',
        'REDIS_CACHE_URL': 'redis://localhost:6379/0',
        'RECOMMENDATION_TOP_N': '5',
        'RECOMMENDATION_MIN_SIMILARITY': '0.1',
        'ENVIRONMENT': 'test'
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

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
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
