
import os
from urllib.parse import urlparse, urlunparse

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

parsed = urlparse(DB_URL)
if parsed.password:
    masked = parsed._replace(
        netloc=f"{parsed.username}:****@{parsed.hostname}:{parsed.port}"
    )
    url_display = urlunparse(masked)
else:
    url_display = DB_URL
print(f"Testing connection to: {url_display}")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("Connection SUCCESSFUL")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Connection FAILED: {e}")
