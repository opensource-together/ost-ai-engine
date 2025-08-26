#!/usr/bin/env python3
"""
Script pour peupler les tables de référence CATEGORY et TECH_STACK.
Ce script peut être exécuté indépendamment pour initialiser les données de référence.
"""

import sys
import os
import uuid
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy import text
from src.infrastructure.postgres.database import get_db_session

# Categories from prisma.service.ts
CATEGORIES = [
    "IA & Machine Learning", "Développement Web", "Applications Mobile", 
    "DevOps & Cloud", "Jeux Vidéo", "Blockchain & Crypto", "E-commerce", 
    "Fintech", "Santé & Médecine", "Éducation", "Réseaux Sociaux", 
    "Productivité", "Sécurité & Cybersécurité", "IoT & Hardware", 
    "Data Science & Analytics", "Outils Développeur", 
    "API & Microservices", "Open Source Tools"
]

# Essential tech stacks (selection from prisma.service.ts)
TECH_STACKS = [
    # Langages
    ("Python", "LANGUAGE"), ("JavaScript", "LANGUAGE"), ("TypeScript", "LANGUAGE"),
    ("Java", "LANGUAGE"), ("Go", "LANGUAGE"), ("Rust", "LANGUAGE"),
    ("C++", "LANGUAGE"), ("C#", "LANGUAGE"), ("PHP", "LANGUAGE"), ("C", "LANGUAGE"),
    ("Kotlin", "LANGUAGE"), ("Swift", "LANGUAGE"), ("Ruby", "LANGUAGE"),
    ("Dart", "LANGUAGE"), ("HTML", "LANGUAGE"), ("CSS", "LANGUAGE"),
    # Frameworks/Tech
    ("React", "TECH"), ("Node.js", "TECH"), ("Next.js", "TECH"), ("Angular", "TECH"),
    ("Vue.js", "TECH"), ("Django", "TECH"), ("Flask", "TECH"), ("Express", "TECH"),
    ("Nest.js", "TECH"), ("Spring Boot", "TECH"), ("Laravel", "TECH"),
    ("Docker", "TECH"), ("Kubernetes", "TECH"), ("PostgreSQL", "TECH"), 
    ("MongoDB", "TECH"), ("Redis", "TECH"), ("MySQL", "TECH")
]

def populate_reference_tables():
    """Populate CATEGORY and TECH_STACK reference tables with standard data."""
    print("🏗️ Starting reference tables population")
    print(f"📋 Categories to populate: {len(CATEGORIES)}")
    print(f"⚙️ Tech stacks to populate: {len(TECH_STACKS)}")
    
    categories_inserted = 0
    tech_stacks_inserted = 0
    
    with get_db_session() as db:
        # Populate CATEGORY table
        for category in CATEGORIES:
            category_id = str(uuid.uuid4())
            result = db.execute(text("""
                INSERT INTO "CATEGORY" (id, name, created_at) 
                VALUES (:id, :name, NOW())
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """), {"id": category_id, "name": category})
            if result.fetchone():
                categories_inserted += 1
        
        # Populate TECH_STACK table
        for name, type_val in TECH_STACKS:
            tech_id = str(uuid.uuid4())
            result = db.execute(text("""
                INSERT INTO "TECH_STACK" (id, name, type, created_at) 
                VALUES (:id, :name, :type, NOW())
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """), {"id": tech_id, "name": name, "type": type_val})
            if result.fetchone():
                tech_stacks_inserted += 1
        
        db.commit()
    
    # Verify final counts
    with get_db_session() as db:
        total_categories = db.execute(text('SELECT COUNT(*) FROM "CATEGORY"')).scalar()
        total_tech_stacks = db.execute(text('SELECT COUNT(*) FROM "TECH_STACK"')).scalar()
    
    # Summary logs
    print(f"🎉 Reference tables population completed!")
    print(f"📂 Categories: {categories_inserted} new / {total_categories} total")
    print(f"⚙️ Tech stacks: {tech_stacks_inserted} new / {total_tech_stacks} total")
    print(f"✅ Reference data ready for project mapping...")
    
    return {
        "categories_inserted": categories_inserted,
        "tech_stacks_inserted": tech_stacks_inserted,
        "total_categories": total_categories,
        "total_tech_stacks": total_tech_stacks,
    }

if __name__ == "__main__":
    populate_reference_tables()
