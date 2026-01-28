#!/bin/bash
set -e

echo "Starting initialization..."

# Wait for Postgres
echo "⏳ Waiting for Postgres to be ready..."
# Use Python to check connection using standard environment variables or default values.
# This avoids needing 'postgresql-client' and hardcoded hostnames.
until python3 -c "
import sys, os, time, psycopg2
from urllib.parse import urlparse

url = os.getenv('DATABASE_URL')
user = os.getenv('POSTGRES_USER', 'postgres')
password = os.getenv('POSTGRES_PASSWORD', 'password')
db = os.getenv('POSTGRES_DB', 'ost_db')
host = os.getenv('POSTGRES_HOST', 'db')
port = os.getenv('POSTGRES_PORT', '5432')

# Prefer DATABASE_URL if available
dsn = url if url else f'dbname={db} user={user} password={password} host={host} port={port}'

try:
    conn = psycopg2.connect(dsn)
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'Waiting for DB... {e}')
    sys.exit(1)
"; do
  echo "Sleeping 2s..."
  sleep 2
done
echo "✅ Postgres is ready."

# DBT
if [ -d "dbt" ]; then
    echo "Installing dbt dependencies..."
    cd dbt
    dbt deps
    
    echo "Building dbt models..."
    dbt build
    cd ..
else
    echo "dbt directory not found!"
fi

# Run the command passed to docker
echo "Executing command: $@"
exec "$@"
