#!/usr/bin/env python3
"""
Script pour créer des utilisateurs de test avec différents profils et les mapper aux catégories.

Ce script:
1. Crée 10 utilisateurs avec des profils logiques et variés
2. Mappe intelligemment ces utilisateurs aux catégories basé sur leur bio/compétences
3. Crée les relations USER_CATEGORY

Usage: python scripts/database/create_test_users.py
"""

import sys
import os
import uuid
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy import text
from src.infrastructure.postgres.database import get_db_session

# Règles de mapping bio/compétences → catégories EXACTEMENT alignées avec recreate_schema.sql
# Catégories existantes dans recreate_schema.sql :
# 'IA & Machine Learning', 'Applications Mobile', 'Applications Web', 'Blockchain & Crypto',
# 'Data & Analytics', 'DevOps & Infrastructure', 'Gaming', 'Security', 'Open Source', 'Education'
USER_CATEGORY_MAPPING = {
    "IA & Machine Learning": [
        "ai", "machine learning", "ml", "neural", "deep learning", "tensorflow", "pytorch",
        "computer vision", "nlp", "ml engineer", "data scientist", "artificial intelligence"
    ],
    "Applications Mobile": [
        "mobile", "ios", "android", "react native", "flutter", "swift", "kotlin", "mobile developer",
        "app development", "smartphone", "tablet"
    ],
    "Applications Web": [
        "web", "frontend", "backend", "fullstack", "react", "vue", "angular", "node.js", "nodejs",
        "django", "flask", "api", "graphql", "javascript", "typescript", "html", "css"
    ],
    "Blockchain & Crypto": [
        "blockchain", "crypto", "ethereum", "bitcoin", "smart contract", "solidity", "web3", "defi",
        "cryptocurrency", "nft", "dao"
    ],
    "Data & Analytics": [
        "data", "analytics", "statistics", "analysis", "dataset", "pandas", "numpy", "jupyter", "bi",
        "business intelligence", "data engineering", "etl", "data warehouse"
    ],
    "DevOps & Infrastructure": [
        "devops", "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "infrastructure",
        "terraform", "ansible", "jenkins", "gitlab", "monitoring", "logging"
    ],
    "Gaming": [
        "gaming", "game development", "unity", "unreal", "game engine", "godot", "game design",
        "3d modeling", "game programming", "indie games"
    ],
    "Security": [
        "security", "cybersecurity", "penetration testing", "ethical hacker", "security engineer", "pentest",
        "vulnerability", "threat", "incident response", "compliance", "audit"
    ],
    "Open Source": [
        "open source", "contributor", "maintainer", "oss", "community", "github", "git",
        "free software", "foss", "contribution"
    ],
    "Education": [
        "education", "teaching", "learning", "tutorial", "course", "instructor", "mentor",
        "academic", "research", "university", "bootcamp", "workshop"
    ],
}

# Mapping bio/compétences → tech stacks (basé sur TECH_STACKS de reference_assets.py)
USER_TECH_STACK_MAPPING = {
    # Languages
    "Python": ["python", "pandas", "numpy", "jupyter", "tensorflow", "pytorch", "django", "flask"],
    "JavaScript": ["javascript", "js", "react", "vue", "angular", "node.js", "nodejs", "express"],
    "TypeScript": ["typescript", "ts"],
    "Java": ["java", "spring boot"],
    "Go": ["go", "golang"],
    "Rust": ["rust"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"],
    "PHP": ["php", "laravel"],
    "C": ["c programming"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],
    "Ruby": ["ruby"],
    "Dart": ["dart", "flutter"],
    "HTML": ["html"],
    "CSS": ["css"],
    
    # Technologies
    "React": ["react", "react.js", "reactjs"],
    "Node.js": ["node.js", "nodejs", "express"],
    "Next.js": ["next.js", "nextjs"],
    "Angular": ["angular"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Express": ["express"],
    "Nest.js": ["nest.js", "nestjs"],
    "Spring Boot": ["spring boot", "springboot"],
    "Laravel": ["laravel"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "PostgreSQL": ["postgresql", "postgres"],
}

# Profils d'utilisateurs de test avec des bios réalistes et cohérentes
TEST_USERS = [
    {
        "username": "alice_ml",
        "email": "alice.ml@example.com",
        "login": "alice-ml",
        "bio": "Senior ML Engineer at TechCorp AI with 6+ years experience in deep learning and computer vision. Previously at Google AI working on TensorFlow. Passionate about healthcare AI applications and open source ML tools. Love PyTorch, computer vision, and mentoring junior developers.",
        "location": "San Francisco, CA",
        "company": "TechCorp AI"
    },
    {
        "username": "bob_webdev",
        "email": "bob.webdev@example.com", 
        "login": "bob-webdev",
        "bio": "Full-stack web developer with 8+ years building scalable applications. Expert in React, TypeScript, Node.js, and Python. Led development of high-traffic e-commerce platforms. Currently working on microservices architecture and GraphQL APIs. Open source contributor to Vue.js ecosystem.",
        "location": "New York, NY",
        "company": "WebSolutions Inc"
    },
    {
        "username": "carol_devops",
        "email": "carol.devops@example.com",
        "login": "carol-devops", 
        "bio": "DevOps engineer and cloud architect with 7 years experience. AWS Solutions Architect certified. Specializing in Kubernetes, Docker, and infrastructure as code with Terraform. Built CI/CD pipelines for Fortune 500 companies. Passionate about monitoring, observability, and SRE practices.",
        "location": "Austin, TX",
        "company": "CloudTech"
    },
    {
        "username": "dave_security",
        "email": "dave.security@example.com",
        "login": "dave-security",
        "bio": "Cybersecurity expert and ethical hacker with 10+ years in penetration testing and security audits. OSCP and CISSP certified. Former security consultant for financial institutions. Specializing in application security, threat modeling, and incident response. Regular speaker at security conferences.",
        "location": "Seattle, WA", 
        "company": "SecureNet"
    },
    {
        "username": "eve_data",
        "email": "eve.data@example.com",
        "login": "eve-data",
        "bio": "Senior Data Scientist with PhD in Statistics. Expert in pandas, numpy, and building data-driven solutions. Led analytics teams at multiple startups. Specializing in business intelligence, predictive modeling, and data engineering. Created several popular data science tutorials and courses.",
        "location": "Boston, MA",
        "company": "DataInsights"
    },
    {
        "username": "frank_mobile",
        "email": "frank.mobile@example.com",
        "login": "frank-mobile",
        "bio": "Mobile app developer with 5+ years creating iOS and Android applications. Expert in React Native, Flutter, and native development. Built apps with millions of downloads. Passionate about mobile UX/UI design and cross-platform development. Regular contributor to mobile development communities.",
        "location": "Los Angeles, CA",
        "company": "MobileFirst"
    },
    {
        "username": "grace_blockchain",
        "email": "grace.blockchain@example.com",
        "login": "grace-blockchain",
        "bio": "Blockchain developer and DeFi protocol architect with 4 years experience. Expert in Solidity, Ethereum, and smart contract development. Built multiple successful DeFi protocols and NFT marketplaces. Passionate about Web3, DAOs, and decentralized applications. Regular speaker at blockchain conferences.",
        "location": "Miami, FL",
        "company": "CryptoVentures"
    },
    {
        "username": "henry_opensource",
        "email": "henry.opensource@example.com",
        "login": "henry-oss",
        "bio": "Open source maintainer and contributor for 8+ years. Core contributor to several major projects including React, Node.js, and various developer tools. Built popular open source libraries with 10k+ stars on GitHub. Passionate about developer experience and building tools that help the community.",
        "location": "Portland, OR",
        "company": "OpenSource Labs"
    },
    {
        "username": "iris_education",
        "email": "iris.education@example.com",
        "login": "iris-edu",
        "bio": "Tech educator and course creator with 6 years experience teaching programming and data science. Created online courses with 50k+ students. Former university professor and bootcamp instructor. Specializing in Python, JavaScript, and data science education. Passionate about making tech accessible to everyone.",
        "location": "Chicago, IL",
        "company": "CodeAcademy"
    },
    {
        "username": "jack_gaming",
        "email": "jack.gaming@example.com",
        "login": "jack-gaming",
        "bio": "Game developer and 3D artist with 7 years experience in Unity and Unreal Engine. Created multiple indie games and worked on AAA titles. Expert in game programming, 3D modeling, and game design. Passionate about indie game development and helping new developers enter the gaming industry.",
        "location": "Denver, CO",
        "company": "IndieGame Studio"
    }
]

def clean_existing_test_users():
    """Clean existing test users and their relations before creating new ones."""
    with get_db_session() as db:
        # Get usernames from TEST_USERS
        test_usernames = [u["username"] for u in TEST_USERS]
        
        print(f"🧹 Cleaning existing test users: {test_usernames}")
        
        # Delete user-tech_stack relations first (foreign key constraint)
        deleted_tech_relations = db.execute(text("""
            DELETE FROM "USER_TECH_STACK" 
            WHERE user_id IN (
                SELECT id FROM "USER" WHERE username = ANY(:usernames)
            )
        """), {"usernames": test_usernames}).rowcount
        
        # Delete user-category relations first (foreign key constraint)
        deleted_relations = db.execute(text("""
            DELETE FROM "USER_CATEGORY" 
            WHERE user_id IN (
                SELECT id FROM "USER" WHERE username = ANY(:usernames)
            )
        """), {"usernames": test_usernames}).rowcount
        
        # Delete users
        deleted_users = db.execute(text("""
            DELETE FROM "USER" 
            WHERE username = ANY(:usernames)
        """), {"usernames": test_usernames}).rowcount
        
        db.commit()
        print(f"✅ Cleaned {deleted_users} users, {deleted_relations} user-category relations, and {deleted_tech_relations} user-tech_stack relations")

def verify_tables_exist():
    """Verify that required tables exist (created by recreate_schema.sql)"""
    with get_db_session() as db:
        # Check if required tables exist
        tables_to_check = ["USER_CATEGORY", "USER_TECH_STACK", "CATEGORY", "TECH_STACK"]
        
        for table in tables_to_check:
            result = db.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                )
            """)).scalar()
            
            if result:
                print(f"✅ {table} table exists")
            else:
                print(f"❌ {table} table not found")
                raise Exception(f"{table} table not found. Please run recreate_schema.sql first")
        
        print("✅ All required tables verified")

def create_test_users():
    """Create test users with realistic profiles"""
    with get_db_session() as db:
        created_users = []
        
        for user_data in TEST_USERS:
            user_id = str(uuid.uuid4())
            
            # Insert user
            result = db.execute(text("""
                INSERT INTO "USER" (id, username, email, login, bio, location, company, created_at, updated_at)
                VALUES (:id, :username, :email, :login, :bio, :location, :company, NOW(), NOW())
                ON CONFLICT (username) DO NOTHING
                RETURNING id
            """), {
                "id": user_id,
                "username": user_data["username"],
                "email": user_data["email"],
                "login": user_data["login"],
                "bio": user_data["bio"],
                "location": user_data["location"],
                "company": user_data["company"]
            })
            
            result_row = result.fetchone()
            if result_row:
                created_users.append({
                    "id": user_id,
                    "username": user_data["username"],
                    "bio": user_data["bio"]
                })
                print(f"✅ Created user: {user_data['username']}")
        
        db.commit()
        print(f"📊 Created {len(created_users)} test users")
        return created_users

def _fetch_test_users_from_db(db):
    """Fetch all test users (by usernames from TEST_USERS) from DB with id and bio."""
    usernames = [u["username"] for u in TEST_USERS]
    rows = db.execute(text("""
        SELECT id, username, COALESCE(bio, '') as bio
        FROM "USER"
        WHERE username = ANY(:usernames)
        ORDER BY username
    """), {"usernames": usernames}).fetchall()
    return [{"id": str(r[0]), "username": r[1], "bio": r[2]} for r in rows]


def map_users_to_categories(users):
    """Map users to categories based on their bio and expertise (idempotent)."""
    with get_db_session() as db:
        # If no newly created users (due to ON CONFLICT), fetch existing test users
        if not users:
            users = _fetch_test_users_from_db(db)

        total_mappings = 0

        for user in users:
            user_id = user["id"]
            bio = (user["bio"] or "").lower()
            username = user["username"]

            matched_categories = set()

            # Find matching categories based on bio
            for category, keywords in USER_CATEGORY_MAPPING.items():
                if any(keyword in bio for keyword in keywords):
                    matched_categories.add(category)

            # Insert category mappings
            category_count = 0
            for category_name in matched_categories:
                category_result = db.execute(text("""
                    SELECT id FROM "CATEGORY" WHERE name = :name
                """), {"name": category_name}).fetchone()

                if category_result:
                    db.execute(text("""
                        INSERT INTO "USER_CATEGORY" (user_id, category_id)
                        VALUES (:user_id, :category_id)
                        ON CONFLICT DO NOTHING
                    """), {"user_id": user_id, "category_id": category_result[0]})
                    category_count += 1

            total_mappings += category_count
            print(f"🎯 '{username}' → {category_count} categories: {list(matched_categories)}")

        db.commit()
        print(f"📊 Total user-category mappings created: {total_mappings}")

def map_users_to_tech_stacks(users):
    """Map users to tech stacks based on their bio and expertise (idempotent)."""
    with get_db_session() as db:
        # If no users provided, fetch existing test users
        if not users:
            users = _fetch_test_users_from_db(db)

        total_mappings = 0

        for user in users:
            user_id = user["id"]
            bio = (user["bio"] or "").lower()
            username = user["username"]

            matched_tech_stacks = set()

            # Find matching tech stacks based on bio
            for tech_stack, keywords in USER_TECH_STACK_MAPPING.items():
                if any(keyword in bio for keyword in keywords):
                    matched_tech_stacks.add(tech_stack)

            # Insert tech stack mappings
            tech_count = 0
            for tech_stack_name in matched_tech_stacks:
                tech_result = db.execute(text("""
                    SELECT id FROM "TECH_STACK" WHERE name = :name
                """), {"name": tech_stack_name}).fetchone()

                if tech_result:
                    db.execute(text("""
                        INSERT INTO "USER_TECH_STACK" (user_id, tech_stack_id)
                        VALUES (:user_id, :tech_stack_id)
                        ON CONFLICT DO NOTHING
                    """), {"user_id": user_id, "tech_stack_id": tech_result[0]})
                    tech_count += 1

            total_mappings += tech_count
            print(f"⚙️  '{username}' → {tech_count} tech stacks: {list(matched_tech_stacks)}")

        db.commit()
        print(f"📊 Total user-tech_stack mappings created: {total_mappings}")

def verify_user_creation():
    """Verify the created users and their category mappings"""
    with get_db_session() as db:
        # Count users
        user_count = db.execute(text('SELECT COUNT(*) FROM "USER"')).scalar()
        print(f"📊 Total users: {user_count}")
        
        # Count user-category relations
        relation_count = db.execute(text('SELECT COUNT(*) FROM "USER_CATEGORY"')).scalar()
        print(f"📊 Total USER_CATEGORY relations: {relation_count}")
        
        # Count user-tech_stack relations
        tech_relation_count = db.execute(text('SELECT COUNT(*) FROM "USER_TECH_STACK"')).scalar()
        print(f"📊 Total USER_TECH_STACK relations: {tech_relation_count}")
        
        # Show sample mappings
        sample = db.execute(text("""
            SELECT u.username, u.bio,
                   STRING_AGG(DISTINCT c.name, ', ') as categories,
                   STRING_AGG(DISTINCT ts.name, ', ') as tech_stacks
            FROM "USER" u 
            LEFT JOIN "USER_CATEGORY" uc ON u.id = uc.user_id 
            LEFT JOIN "CATEGORY" c ON uc.category_id = c.id 
            LEFT JOIN "USER_TECH_STACK" uts ON u.id = uts.user_id
            LEFT JOIN "TECH_STACK" ts ON uts.tech_stack_id = ts.id
            GROUP BY u.id, u.username, u.bio 
            ORDER BY u.username
        """)).fetchall()
        
        print("\n📋 Sample user-category-tech mappings:")
        for row in sample:
            username, bio, categories, tech_stacks = row
            print(f"• {username}")
            print(f"  └─ Bio: {bio[:80]}...")
            print(f"  └─ Categories: {categories or 'none'}")
            print(f"  └─ Tech Stacks: {tech_stacks or 'none'}")

if __name__ == "__main__":
    print("🚀 Creating test users and mapping to categories...")
    
    # Step 1: Clean existing test users
    clean_existing_test_users()

    # Step 2: Verify required tables exist
    verify_tables_exist()
    
    # Step 3: Create test users
    users = create_test_users()
    
    # Step 4: Map users to categories
    if users:
        map_users_to_categories(users)
    
    # Step 5: Map users to tech stacks
    if users:
        map_users_to_tech_stacks(users)
    
    # Step 6: Verify results
    verify_user_creation()
    
    print("✅ Test users creation completed!")
