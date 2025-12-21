from src.services.python.db import get_db_cursor
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def audit():
    with get_db_cursor() as cur:
        print("--- Classification Stats ---")
        cur.execute('SELECT COUNT(*) as count, AVG("categoryConfidence") as avg_cat, MIN("categoryConfidence") as min_cat, MAX("categoryConfidence") as max_cat FROM "match"."project_classification"')
        stats = cur.fetchone()
        print(stats)

        print("\n--- Sample Classifications ---")
        cur.execute('SELECT "projectId", "categoryConfidence", "domainConfidence" FROM "match"."project_classification" LIMIT 5')
        rows = cur.fetchall()
        for r in rows:
            print(r)

        print("\n--- Sample Project Contexts (Input for Embedding) ---")
        # Assuming int_github_embedding has 'context' column
        try:
            cur.execute('SELECT "id", "context" FROM "github"."int_github_embedding" LIMIT 3')
            contexts = cur.fetchall()
            for c in contexts:
                print(f"Project ID: {c['id']}")
                print(f"Context (Preview): {c['context'][:200]}...") # Print first 200 chars
                print("-" * 20)
        except Exception as e:
            print(f"Could not query int_github_embedding: {e}")

        print("\n--- Sample Category Contexts ---")
        try:
            cur.execute('SELECT "id", "context" FROM "ml"."int_category_embedding" LIMIT 3')
            cats = cur.fetchall()
            for c in cats:
                 print(f"Category Context: {c['context']}")
        except Exception as e:
            print(f"Could not query int_category_embedding: {e}")

if __name__ == "__main__":
    audit()
