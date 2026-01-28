#!/bin/bash
set -e

echo "Starting initialization..."

# Wait for Postgres
echo "Waiting for Postgres to be ready..."
until pg_isready -h db -p 5432 -U "${POSTGRES_USER}"; do
  echo "Sleeping 2s..."
  sleep 2
done
echo "Postgres is ready."

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
