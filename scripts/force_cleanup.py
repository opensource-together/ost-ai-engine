from src.services.python.db import get_db_cursor
from dotenv import load_dotenv
import os

load_dotenv()

def force_clean():
    try:
        with get_db_cursor(commit=True) as cur:
            print("Dropping dependencies CASCADE...")
            # Drop views that might depend on pvt_github_project
            cur.execute('DROP VIEW IF EXISTS "public"."prd_github_project" CASCADE')
            cur.execute('DROP TABLE IF EXISTS "github"."pvt_github_project" CASCADE')
            print("Done.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_clean()
