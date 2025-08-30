#!/usr/bin/env python3
"""
Test database setup script.
Creates minimal schema and test data for CI testing.
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from src.infrastructure.config import settings


def setup_test_database():
    """Setup test database with minimal schema and test data."""
    print("🔧 Setting up test database...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create extensions
        print("  📦 Creating PostgreSQL extensions...")
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        
        # Create minimal schema for tests
        print("  🏗️  Creating test tables...")
        
        # USER table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS "USER" (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                username VARCHAR(30) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        '''))
        
        # PROJECT table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS "PROJECT" (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                title VARCHAR(100) NOT NULL,
                description TEXT,
                primary_language VARCHAR(50),
                stargazers_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        '''))
        
        # USER_PROJECT_SIMILARITY table
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
        print("  📊 Inserting test data...")
        
        # Test users
        conn.execute(text('''
            INSERT INTO "USER" (id, username, email) VALUES 
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, 'test_user_1', 'user1@test.com'),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, 'test_user_2', 'user2@test.com'),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, 'test_user_3', 'user3@test.com')
            ON CONFLICT (username) DO NOTHING
        '''))
        
        # Test projects
        conn.execute(text('''
            INSERT INTO "PROJECT" (id, title, description, primary_language, stargazers_count) VALUES 
            ('123e4567-e89b-12d3-a456-426614174003'::uuid, 'Python ML Project', 'Machine learning project in Python', 'Python', 1500),
            ('123e4567-e89b-12d3-a456-426614174004'::uuid, 'JavaScript Web App', 'Modern web application', 'JavaScript', 800),
            ('123e4567-e89b-12d3-a456-426614174005'::uuid, 'Go Microservice', 'High-performance microservice', 'Go', 1200),
            ('123e4567-e89b-12d3-a456-426614174006'::uuid, 'Data Science Tool', 'Data analysis and visualization', 'Python', 2000),
            ('123e4567-e89b-12d3-a456-426614174007'::uuid, 'React Component Library', 'Reusable React components', 'TypeScript', 950)
            ON CONFLICT (id) DO NOTHING
        '''))
        
        # Test similarity data
        conn.execute(text('''
            INSERT INTO "USER_PROJECT_SIMILARITY" (user_id, project_id, similarity_score, semantic_similarity, category_similarity, language_similarity, popularity_similarity) VALUES 
            -- User 1 (Python developer) - high similarity with Python projects
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174003'::uuid, 0.92, 0.88, 0.95, 0.90, 0.85),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174006'::uuid, 0.89, 0.85, 0.92, 0.88, 0.90),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174004'::uuid, 0.65, 0.60, 0.70, 0.55, 0.75),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174005'::uuid, 0.72, 0.68, 0.75, 0.65, 0.80),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174007'::uuid, 0.58, 0.55, 0.62, 0.50, 0.70),
            
            -- User 2 (JavaScript developer) - high similarity with JS/TS projects
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174004'::uuid, 0.94, 0.90, 0.96, 0.92, 0.80),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174007'::uuid, 0.91, 0.87, 0.93, 0.89, 0.85),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174003'::uuid, 0.68, 0.65, 0.72, 0.60, 0.75),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174005'::uuid, 0.75, 0.72, 0.78, 0.68, 0.82),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174006'::uuid, 0.62, 0.58, 0.65, 0.55, 0.70),
            
            -- User 3 (Go developer) - high similarity with Go projects
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174005'::uuid, 0.96, 0.93, 0.98, 0.95, 0.85),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174003'::uuid, 0.78, 0.75, 0.82, 0.70, 0.80),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174004'::uuid, 0.71, 0.68, 0.75, 0.65, 0.75),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174006'::uuid, 0.69, 0.66, 0.72, 0.62, 0.78),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174007'::uuid, 0.64, 0.61, 0.68, 0.58, 0.72)
            ON CONFLICT (user_id, project_id) DO NOTHING
        '''))
        
        conn.commit()
        
        # Verify setup
        print("  ✅ Verifying setup...")
        result = conn.execute(text('SELECT COUNT(*) FROM "USER"'))
        user_count = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM "PROJECT"'))
        project_count = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM "USER_PROJECT_SIMILARITY"'))
        similarity_count = result.scalar()
        
        print(f"  📊 Test data created:")
        print(f"     Users: {user_count}")
        print(f"     Projects: {project_count}")
        print(f"     Similarities: {similarity_count}")
        
    print("✅ Test database setup completed!")


if __name__ == "__main__":
    setup_test_database()
