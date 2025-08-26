import uuid
from typing import List

from dagster import asset, AssetIn, Output, Nothing
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

# Mapping rules: topics + description → categories
CATEGORY_MAPPING = {
    "Éducation": ["education", "books", "learning", "tutorial", "course", "study"],
    "Outils Développeur": ["development", "programming", "developer", "tools", "framework", "design-patterns"],
    "API & Microservices": ["api", "apis", "microservices", "rest", "graphql", "public-api"],
    "Open Source Tools": ["open-source", "opensource", "free", "public", "hacktoberfest"],
    "IA & Machine Learning": ["ai", "machine-learning", "ml", "neural", "deep-learning"],
    "Data Science & Analytics": ["data", "analytics", "statistics", "analysis", "dataset"],
    "Développement Web": ["web", "webapp", "website", "frontend", "backend", "web-application"],
    "DevOps & Cloud": ["devops", "cloud", "aws", "deployment", "infrastructure"],
    "Sécurité & Cybersécurité": ["security", "cybersecurity", "encryption", "authentication"],
    "Productivité": ["productivity", "tools", "workflow"],
    "Réseaux Sociaux": ["social", "community", "networking"]
}

@asset(
    name="project_mappings",
    description="Map existing projects to categories and tech stacks using intelligent text analysis",
    ins={
        "github_data": AssetIn("github_data_ready", dagster_type=Nothing),
        "project_data": AssetIn("dbt_projects", dagster_type=Nothing)  # Attend dbt_projects dbt model
    },
    group_name="reference_data", 
    compute_kind="python",
)
def project_mappings(context) -> Output[dict]:
    """
    Maps existing projects to categories and tech stacks based on intelligent analysis
    of project topics, descriptions, and primary language.
    """
    context.log.info(f"🎯 Starting intelligent project mapping")
    context.log.info(f"📊 Using pre-populated reference tables (CATEGORY, TECH_STACK)")
    
    category_mappings = 0
    tech_mappings = 0
    projects_processed = 0
    
    with get_db_session() as db:
        # Get projects with their topics
        projects = db.execute(text("""
            SELECT id, title, description, topics, primary_language 
            FROM "PROJECT"
        """)).fetchall()
        
        context.log.info(f"🔍 Found {len(projects)} projects to analyze and map")
        
        for i, project in enumerate(projects, 1):
            project_id, title, desc, topics, lang = project
            matched_categories = set()
            projects_processed += 1
            
            context.log.info(f"🧠 [{i}/{len(projects)}] Analyzing: {title} ({lang or 'unknown'})")
            
            # Combine topics and description for analysis
            text_to_analyze = (desc or "").lower() + " " + " ".join(topics or [])
            
            # Find matching categories
            for category, keywords in CATEGORY_MAPPING.items():
                if any(kw in text_to_analyze for kw in keywords):
                    matched_categories.add(category)
            
            context.log.debug(f"   📂 Matched categories: {list(matched_categories) if matched_categories else 'None'}")
            context.log.debug(f"   🔧 Primary language: {lang or 'None'}")
            
            # Insert category mappings
            for category_name in matched_categories:
                category_result = db.execute(text("""
                    SELECT id FROM "CATEGORY" WHERE name = :name
                """), {"name": category_name}).fetchone()
                
                if category_result:
                    result = db.execute(text("""
                        INSERT INTO "PROJECT_CATEGORY" (project_id, category_id)
                        VALUES (:project_id, :category_id)
                        ON CONFLICT DO NOTHING
                        RETURNING project_id
                    """), {"project_id": project_id, "category_id": category_result[0]})
                    if result.fetchone():
                        category_mappings += 1
            
            # Map primary language to tech stack
            if lang:
                tech_result = db.execute(text("""
                    SELECT id FROM "TECH_STACK" WHERE name = :name
                """), {"name": lang}).fetchone()
                
                if tech_result:
                    result = db.execute(text("""
                        INSERT INTO "PROJECT_TECH_STACK" (project_id, tech_stack_id)
                        VALUES (:project_id, :tech_stack_id)
                        ON CONFLICT DO NOTHING
                        RETURNING project_id
                    """), {"project_id": project_id, "tech_stack_id": tech_result[0]})
                    if result.fetchone():
                        tech_mappings += 1
            
            context.log.info(f"   ✅ Mapped to {len(matched_categories)} categories, tech: {1 if lang else 0}")
        
        db.commit()
    
    # Verify final counts
    with get_db_session() as db:
        total_category_relations = db.execute(text('SELECT COUNT(*) FROM "PROJECT_CATEGORY"')).scalar()
        total_tech_relations = db.execute(text('SELECT COUNT(*) FROM "PROJECT_TECH_STACK"')).scalar()
    
    # Summary logs
    context.log.info(f"🎉 Project mapping completed successfully!")
    context.log.info(f"📊 Projects processed: {projects_processed}")
    context.log.info(f"📂 New category mappings: {category_mappings}")
    context.log.info(f"⚙️ New tech stack mappings: {tech_mappings}")
    context.log.info(f"📈 Total category relations: {total_category_relations}")
    context.log.info(f"🔧 Total tech relations: {total_tech_relations}")
    context.log.info(f"✅ Data ready for ML training preparation...")
    
    return Output(
        {
            "projects_processed": projects_processed,
            "category_mappings": category_mappings,
            "tech_mappings": tech_mappings,
            "total_category_relations": total_category_relations,
            "total_tech_relations": total_tech_relations,
        },
        metadata={
            "projects_processed": projects_processed,
            "category_mappings": category_mappings,
            "tech_mappings": tech_mappings,
            "total_category_relations": total_category_relations,
            "total_tech_relations": total_tech_relations,
        }
    )


@asset(
    name="mappings_ready",
    description="Checkpoint: ensures all project mappings are completed before training data creation",
    ins={"mapping_data": AssetIn("project_mappings")},
    group_name="reference_data",
    compute_kind="python",
)
def mappings_ready(context, mapping_data: dict) -> Output[dict]:
    """
    Simple checkpoint asset that confirms project mapping is complete.
    This forces embed_PROJECTS (dbt) to wait for all mappings.
    """
    from src.infrastructure.postgres.database import get_db_session
    from sqlalchemy import text
    
    with get_db_session() as db:
        category_count = db.execute(text('SELECT COUNT(*) FROM "PROJECT_CATEGORY"')).scalar()
        tech_count = db.execute(text('SELECT COUNT(*) FROM "PROJECT_TECH_STACK"')).scalar()
        
    context.log.info(f"✅ Mapping checkpoint: {category_count} project-category, {tech_count} project-tech relations")
    context.log.info(f"🚀 Ready for embedding data creation...")
    
    return Output(
        {"category_relations": category_count, "tech_relations": tech_count},
        metadata={"category_relations": category_count, "tech_relations": tech_count}
    )
