from src.services.python.db import get_db_cursor
from dotenv import load_dotenv
import os

load_dotenv()

def list_tables():
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row['table_name'] for row in cur.fetchall()]
            print("Tables in public schema:", tables)
            
            # Check specifically for authenticator or project_category
            if 'authenticator' in tables:
                print("Found 'authenticator' table.")
            if 'project_category' in tables:
                print("Found 'project_category' table.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables()
