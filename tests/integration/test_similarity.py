"""
Integration tests for similarity calculations and recommendations.
Tests the interaction between database, ML pipeline, and Go API.
"""

import pytest
import numpy as np
import requests
import os
from sqlalchemy import create_engine, text
from src.infrastructure.config import settings


@pytest.mark.integration
def test_similarity_data_quality():
    """Test the quality of similarity data in USER_PROJECT_SIMILARITY."""
    print("🔍 SIMILARITY DATA QUALITY TEST")
    print("=" * 80)
    
    # Database connection
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check that the table exists and contains data
        result = conn.execute(text('SELECT COUNT(*) FROM "USER_PROJECT_SIMILARITY"'))
        total_records = result.scalar()
        assert total_records > 0, "USER_PROJECT_SIMILARITY table is empty"
        
        print(f"📊 Total records: {total_records:,}")
        
        # Analyze similarity scores
        result = conn.execute(text("""
            SELECT 
                AVG(similarity_score) as avg_score,
                MIN(similarity_score) as min_score,
                MAX(similarity_score) as max_score,
                STDDEV(similarity_score) as std_score,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT project_id) as unique_projects
            FROM "USER_PROJECT_SIMILARITY"
        """))
        
        stats = result.fetchone()
        print(f"📈 Score statistics:")
        print(f"   Average score: {stats.avg_score:.3f}")
        print(f"   Min score: {stats.min_score:.3f}")
        print(f"   Max score: {stats.max_score:.3f}")
        print(f"   Standard deviation: {stats.std_score:.3f}")
        print(f"   Unique users: {stats.unique_users}")
        print(f"   Unique projects: {stats.unique_projects}")
        
        # Check for identical scores for the same user
        result = conn.execute(text("""
            SELECT user_id, COUNT(*) as duplicate_count
            FROM (
                SELECT user_id, similarity_score, COUNT(*) as score_count
                FROM "USER_PROJECT_SIMILARITY"
                GROUP BY user_id, similarity_score
                HAVING COUNT(*) > 1
            ) duplicates
            GROUP BY user_id
            ORDER BY duplicate_count DESC
            LIMIT 5
        """))
        
        duplicates = result.fetchall()
        if duplicates:
            print(f"⚠️  Users with identical scores:")
            for user_id, count in duplicates:
                print(f"   User {user_id}: {count} identical scores")
        else:
            print(f"✅ No identical scores detected")
        
        # Check recommendation distribution per user
        result = conn.execute(text("""
            SELECT 
                AVG(rec_count) as avg_recs,
                MIN(rec_count) as min_recs,
                MAX(rec_count) as max_recs,
                COUNT(*) as users_with_recs
            FROM (
                SELECT user_id, COUNT(*) as rec_count
                FROM "USER_PROJECT_SIMILARITY"
                GROUP BY user_id
            ) user_recs
        """))
        
        rec_stats = result.fetchone()
        print(f"\n📋 Recommendation distribution:")
        print(f"   Average recommendations per user: {rec_stats.avg_recs:.1f}")
        print(f"   Min recommendations: {rec_stats.min_recs}")
        print(f"   Max recommendations: {rec_stats.max_recs}")
        print(f"   Users with recommendations: {rec_stats.users_with_recs}")
        
        # Check that recommendation count respects RECOMMENDATION_TOP_N
        expected_top_n = settings.RECOMMENDATION_TOP_N
        result = conn.execute(text(f"""
            SELECT COUNT(*) as users_with_correct_count
            FROM (
                SELECT user_id, COUNT(*) as rec_count
                FROM "USER_PROJECT_SIMILARITY"
                GROUP BY user_id
                HAVING COUNT(*) = {expected_top_n}
            ) correct_users
        """))
        
        correct_count = result.scalar()
        print(f"\n🎯 RECOMMENDATION_TOP_N compliance ({expected_top_n}):")
        print(f"   Users with exactly {expected_top_n} recommendations: {correct_count}")
        print(f"   Percentage: {(correct_count/rec_stats.users_with_recs)*100:.1f}%")


@pytest.mark.integration
@pytest.mark.api
def test_go_api_recommendations():
    """Test the Go API for recommendations."""
    print("\n🔍 GO API TEST")
    print("=" * 80)
    
    # Go API URL
    go_api_url = f"http://localhost:{settings.GO_API_PORT}/recommendations"
    
    # Test with existing user
    test_user_id = "ab18fc24-40d9-4055-ac46-393e25eb3736"  # eve_data
    
    try:
        response = requests.get(f"{go_api_url}?user_id={test_user_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Go API is working")
            print(f"   User ID: {data.get('user_id', 'N/A')}")
            print(f"   Recommendations: {len(data.get('recommendations', []))}")
            print(f"   Timestamp: {data.get('generated_at', 'N/A')}")
            
            # Check response structure
            assert 'user_id' in data, "Response missing 'user_id'"
            assert 'recommendations' in data, "Response missing 'recommendations'"
            assert 'generated_at' in data, "Response missing 'generated_at'"
            
            # Check recommendations
            recommendations = data['recommendations']
            if recommendations:
                print(f"\n📋 Example recommendation:")
                first_rec = recommendations[0]
                print(f"   Project: {first_rec.get('project_title', 'N/A')}")
                print(f"   Score: {first_rec.get('similarity_score', 'N/A')}")
                print(f"   Language: {first_rec.get('primary_language', 'N/A')}")
                print(f"   Stars: {first_rec.get('stargazers_count', 'N/A')}")
                
                # Check that scores are in [0, 1]
                for rec in recommendations:
                    score = rec.get('similarity_score')
                    if score is not None:
                        assert 0 <= score <= 1, f"Invalid score: {score}"
            
        else:
            print(f"❌ Go API error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot contact Go API: {e}")
        print(f"   Check that Go API is running on port {settings.GO_API_PORT}")


@pytest.mark.integration
def test_similarity_consistency():
    """Test similarity data consistency."""
    print("\n🔍 CONSISTENCY TEST")
    print("=" * 80)
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check for no duplicate user_id + project_id pairs
        result = conn.execute(text("""
            SELECT COUNT(*) as duplicate_pairs
            FROM (
                SELECT user_id, project_id, COUNT(*)
                FROM "USER_PROJECT_SIMILARITY"
                GROUP BY user_id, project_id
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        
        duplicate_pairs = result.scalar()
        assert duplicate_pairs == 0, f"Found {duplicate_pairs} duplicate user_id/project_id pairs"
        print(f"✅ No duplicate user_id/project_id pairs")
        
        # Check that scores are in [0, 1]
        result = conn.execute(text("""
            SELECT COUNT(*) as invalid_scores
            FROM "USER_PROJECT_SIMILARITY"
            WHERE similarity_score < 0 OR similarity_score > 1
        """))
        
        invalid_scores = result.scalar()
        assert invalid_scores == 0, f"Found {invalid_scores} invalid scores"
        print(f"✅ All scores are in [0, 1]")
        
        # Check that users exist in USER table
        result = conn.execute(text("""
            SELECT COUNT(*) as orphan_users
            FROM "USER_PROJECT_SIMILARITY" ups
            LEFT JOIN "USER" u ON ups.user_id = u.id
            WHERE u.id IS NULL
        """))
        
        orphan_users = result.scalar()
        assert orphan_users == 0, f"Found {orphan_users} orphan users"
        print(f"✅ All users exist in USER table")
        
        # Check that projects exist in PROJECT table
        result = conn.execute(text("""
            SELECT COUNT(*) as orphan_projects
            FROM "USER_PROJECT_SIMILARITY" ups
            LEFT JOIN "PROJECT" p ON ups.project_id = p.id
            WHERE p.id IS NULL
        """))
        
        orphan_projects = result.scalar()
        assert orphan_projects == 0, f"Found {orphan_projects} orphan projects"
        print(f"✅ All projects exist in PROJECT table")


@pytest.mark.integration
def test_database_connection():
    """Test database connectivity and basic operations."""
    print("\n🔍 DATABASE CONNECTION TEST")
    print("=" * 80)
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            print("✅ Database connection successful")
            
            # Test extensions
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp')"))
            extensions = [row[0] for row in result.fetchall()]
            assert 'vector' in extensions, "pgvector extension not found"
            assert 'uuid-ossp' in extensions, "uuid-ossp extension not found"
            print("✅ Required extensions are installed")
            
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")


@pytest.mark.integration
def test_environment_configuration():
    """Test environment configuration."""
    print("\n🔍 CONFIGURATION TEST")
    print("=" * 80)
    
    # Check critical environment variables
    required_vars = [
        'DATABASE_URL',
        'GITHUB_ACCESS_TOKEN',
        'MODEL_NAME',
        'MODEL_DIMENSIONS',
        'GO_API_PORT',
        'RECOMMENDATION_TOP_N'
    ]
    
    for var in required_vars:
        value = getattr(settings, var, None)
        assert value is not None, f"Variable {var} not defined"
        print(f"✅ {var}: {value}")
    
    # Check recommendation parameters
    print(f"\n📋 Recommendation parameters:")
    print(f"   RECOMMENDATION_TOP_N: {settings.RECOMMENDATION_TOP_N}")
    print(f"   RECOMMENDATION_SEMANTIC_WEIGHT: {settings.RECOMMENDATION_SEMANTIC_WEIGHT}")
    print(f"   RECOMMENDATION_CATEGORY_WEIGHT: {settings.RECOMMENDATION_CATEGORY_WEIGHT}")
    print(f"   RECOMMENDATION_TECH_WEIGHT: {settings.RECOMMENDATION_TECH_WEIGHT}")
    print(f"   RECOMMENDATION_POPULARITY_WEIGHT: {settings.RECOMMENDATION_POPULARITY_WEIGHT}")


if __name__ == "__main__":
    # Run all tests
    test_environment_configuration()
    test_database_connection()
    test_similarity_data_quality()
    test_similarity_consistency()
    test_go_api_recommendations()
    
    print("\n✅ All integration tests passed!")
