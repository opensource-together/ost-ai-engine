#!/bin/bash
set -e

echo "Starting initialization..."

# Daemon skips dbt init — webserver handles it
if [ "$DAGSTER_ROLE" = "daemon" ]; then
    echo "Daemon role: skipping dbt init."
    echo "Executing command: $@"
    exec "$@"
fi

# API skips dbt init — only needs DB
if [ "$DAGSTER_ROLE" = "api" ]; then
    echo "API role: skipping dbt init."
    echo "Executing command: $@"
    exec "$@"
fi

# Wait for Postgres
echo "Waiting for Postgres to be ready..."
# Use Python to check connection using standard environment variables.
# This avoids needing 'postgresql-client' and hardcoded hostnames.
until python3 -c "
import sys, os, psycopg2

url = os.getenv('DATABASE_URL')
user = os.getenv('POSTGRES_USER', '')
password = os.getenv('POSTGRES_PASSWORD', '')
db = os.getenv('POSTGRES_DB', '')
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
  sleep 2
done
echo "Postgres is ready."

# DBT
if [ -d "dbt" ]; then
    cd dbt

    if [ -f "packages.yml" ]; then
        echo "Installing dbt dependencies..."
        dbt deps
    fi

    echo "Building dbt models..."
    if ! dbt build; then
        echo "WARNING: dbt build failed — some models may be missing. Continuing startup."
    fi

    cd ..
else
    echo "dbt directory not found!"
fi

# Run the command passed to docker
echo "Executing command: $@"
exec "$@"
