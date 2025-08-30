#!/usr/bin/env python3
"""
Fallback script to create test data directly in SQL if dbt fails.
This is used as a backup in CI environments.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from src.infrastructure.config import settings


def setup_test_data_fallback():
    """Setup test data directly in SQL as fallback."""
    print("🔧 Setting up test data using fallback method...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create test users
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS "test_users" (
                id UUID PRIMARY KEY,
                username VARCHAR(30) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                primary_language VARCHAR(50),
                category VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        '''))
        
        conn.execute(text('''
            INSERT INTO "test_users" (id, username, email, primary_language, category) VALUES 
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, 'test_user_1', 'user1@test.com', 'Python', 'Data Science'),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, 'test_user_2', 'user2@test.com', 'JavaScript', 'Web Development'),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, 'test_user_3', 'user3@test.com', 'Go', 'Backend Development')
            ON CONFLICT (username) DO NOTHING
        '''))
        
        # Create test projects
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS "test_projects" (
                id UUID PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                primary_language VARCHAR(50),
                category VARCHAR(100),
                stargazers_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        '''))
        
        conn.execute(text('''
            INSERT INTO "test_projects" (id, title, description, primary_language, category, stargazers_count) VALUES 
            ('123e4567-e89b-12d3-a456-426614174003'::uuid, 'Python ML Project', 'Machine learning project in Python', 'Python', 'Data Science', 1500),
            ('123e4567-e89b-12d3-a456-426614174004'::uuid, 'JavaScript Web App', 'Modern web application', 'JavaScript', 'Web Development', 800),
            ('123e4567-e89b-12d3-a456-426614174005'::uuid, 'Go Microservice', 'High-performance microservice', 'Go', 'Backend Development', 1200),
            ('123e4567-e89b-12d3-a456-426614174006'::uuid, 'Data Science Tool', 'Data analysis and visualization', 'Python', 'Data Science', 2000),
            ('123e4567-e89b-12d3-a456-426614174007'::uuid, 'React Component Library', 'Reusable React components', 'TypeScript', 'Web Development', 950)
            ON CONFLICT (id) DO NOTHING
        '''))
        
        # Create test similarities
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS "test_similarities" (
                user_id UUID REFERENCES "test_users"(id),
                project_id UUID REFERENCES "test_projects"(id),
                similarity_score FLOAT NOT NULL,
                semantic_similarity FLOAT,
                category_similarity FLOAT,
                language_similarity FLOAT,
                popularity_similarity FLOAT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                PRIMARY KEY (user_id, project_id)
            )
        '''))
        
        conn.execute(text('''
            INSERT INTO "test_similarities" (user_id, project_id, similarity_score, semantic_similarity, category_similarity, language_similarity, popularity_similarity) VALUES 
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174003'::uuid, 0.92, 0.88, 0.95, 0.90, 0.75),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174006'::uuid, 0.89, 0.85, 0.92, 0.88, 1.00),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174004'::uuid, 0.65, 0.60, 0.70, 0.55, 0.40),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174005'::uuid, 0.72, 0.68, 0.75, 0.65, 0.60),
            ('123e4567-e89b-12d3-a456-426614174000'::uuid, '123e4567-e89b-12d3-a456-426614174007'::uuid, 0.58, 0.55, 0.62, 0.50, 0.48),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174004'::uuid, 0.94, 0.90, 0.96, 0.92, 0.40),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174007'::uuid, 0.91, 0.87, 0.93, 0.89, 0.48),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174003'::uuid, 0.68, 0.65, 0.72, 0.60, 0.75),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174005'::uuid, 0.75, 0.72, 0.78, 0.68, 0.60),
            ('123e4567-e89b-12d3-a456-426614174001'::uuid, '123e4567-e89b-12d3-a456-426614174006'::uuid, 0.62, 0.58, 0.65, 0.55, 1.00),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174005'::uuid, 0.96, 0.93, 0.98, 0.95, 0.60),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174003'::uuid, 0.78, 0.75, 0.82, 0.70, 0.75),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174004'::uuid, 0.71, 0.68, 0.75, 0.65, 0.40),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174006'::uuid, 0.69, 0.66, 0.72, 0.62, 1.00),
            ('123e4567-e89b-12d3-a456-426614174002'::uuid, '123e4567-e89b-12d3-a456-426614174007'::uuid, 0.64, 0.61, 0.68, 0.58, 0.48)
            ON CONFLICT (user_id, project_id) DO NOTHING
        '''))
        
        conn.commit()
        
        # Verify setup
        print("  ✅ Verifying setup...")
        result = conn.execute(text('SELECT COUNT(*) FROM "test_users"'))
        user_count = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM "test_projects"'))
        project_count = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM "test_similarities"'))
        similarity_count = result.scalar()
        
        print(f"  📊 Test data created:")
        print(f"     Users: {user_count}")
        print(f"     Projects: {project_count}")
        print(f"     Similarities: {similarity_count}")
        
    print("✅ Test data setup completed using fallback method!")


if __name__ == "__main__":
    setup_test_data_fallback()
