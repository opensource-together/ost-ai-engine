from src.services.python.db import get_db_cursor

with get_db_cursor(commit=True) as cur:
    print("Truncating table github.int_github_project to allow migration...")
    cur.execute('TRUNCATE TABLE "github"."int_github_project" CASCADE;')
    print("Done.")
