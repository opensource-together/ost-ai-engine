
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
print(f"Testing connection to: {DB_URL}")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("Connection SUCCESSFUL")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Connection FAILED: {e}")
