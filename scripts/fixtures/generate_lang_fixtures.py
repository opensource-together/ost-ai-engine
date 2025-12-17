import sys
import os
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.python.db import get_db_cursor

def generate_lang_fixtures():
    print("Generating fixtures for github.stg_github_project...")
    
    fixtures = [
        # ... (fixtures content remains same)
    ]

    with get_db_cursor(commit=True) as cur:
        for proj in fixtures:
            # On génère un ID seulement si c'est une nouvelle insertion (si nécessaire)
            # Mais pour l'upsert, PostgreSQL gérera l'ID existant si on n'update pas la PK
            # Check if project exists by URL
            cur.execute('SELECT id FROM "github"."stg_github_project" WHERE url = %s', (proj["url"],))
            existing = cur.fetchone()

            if existing:
                # Update existing project
                cur.execute(
                    """
                    UPDATE "github"."stg_github_project"
                    SET "description" = %s,
                        "stars" = %s,
                        "forks" = %s,
                        "topics" = %s,
                        "updated_at" = NOW()
                    WHERE "url" = %s
                    """,
                    (
                        proj["description"],
                        100,
                        10,
                        json.dumps(["test", "fixture"]),
                        proj["url"]
                    )
                )
                print(f"Updated: {proj['name']}")
            else:
                # Insert new project
                proj_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO "github"."stg_github_project" 
                    ("id", "name", "description", "url", "stars", "forks", "language", "topics", "created_at", "updated_at")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (
                        proj_id,
                        proj["name"],
                        proj["description"],
                        proj["url"],
                        100, 
                        10,  
                        proj["language"],
                        json.dumps(["test", "fixture"]),
                    )
                )
                print(f"Inserted: {proj['name']}")

    print("Done! Fixtures generated.")

if __name__ == "__main__":
    generate_lang_fixtures()
