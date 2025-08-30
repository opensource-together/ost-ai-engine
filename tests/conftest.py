import pytest
from sqlalchemy import create_engine, text
from src.infrastructure.config import settings


@pytest.fixture(scope="session")
def setup_test_database():
    """Setup test database with minimal schema and test data."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create extensions
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        
        # Create minimal schema for tests
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS "USER" (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                username VARCHAR(30) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS "PROJECT" (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                title VARCHAR(100) NOT NULL,
                description TEXT,
                primary_language VARCHAR(50),
                stargazers_count INTEGER DEFAULT 0
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS "USER_PROJECT_SIMILARITY" (
                user_id UUID REFERENCES "USER"(id),
                project_id UUID REFERENCES "PROJECT"(id),
                similarity_score FLOAT NOT NULL,
                semantic_similarity FLOAT,
                category_similarity FLOAT,
                language_similarity FLOAT,
                popularity_similarity FLOAT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                PRIMARY KEY (user_id, project_id)
            )
        '''))
        
        # Insert test data
        conn.execute(text('''
            INSERT INTO "USER" (id, username, email) VALUES 
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, 'test_user_1', 'user1@test.com'),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, 'test_user_2', 'user2@test.com')
            ON CONFLICT (username) DO NOTHING
        '''))
        
        conn.execute(text('''
            INSERT INTO "PROJECT" (id, title, description, primary_language, stargazers_count) VALUES 
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, 'Test Project 1', 'A test project', 'Python', 100),
            ('123e4567-e89b-12d3-a456-426614174003'::uuid, 'Test Project 2', 'Another test project', 'JavaScript', 200)
            ON CONFLICT (id) DO NOTHING
        '''))
        
        conn.execute(text('''
            INSERT INTO "USER_PROJECT_SIMILARITY" (user_id, project_id, similarity_score, semantic_similarity, category_similarity, language_similarity, popularity_similarity) VALUES 
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174002'::uuid, 0.85, 0.75, 0.90, 0.80, 0.70),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174003'::uuid, 0.72, 0.65, 0.85, 0.70, 0.60),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174002'::uuid, 0.92, 0.88, 0.95, 0.85, 0.75),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174003'::uuid, 0.68, 0.60, 0.80, 0.65, 0.55)
            ON CONFLICT (user_id, project_id) DO NOTHING
        '''))
        
        conn.commit()
    
    yield engine
    
    # Cleanup (optional - database is destroyed anyway)
    with engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS "USER_PROJECT_SIMILARITY" CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS "PROJECT" CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS "USER" CASCADE'))
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
