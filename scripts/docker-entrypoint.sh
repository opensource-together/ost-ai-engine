#!/bin/sh
set -e

python ./config/cfg.py

if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Starting database setup..."
  echo "Running Prisma migrations..."
  npx prisma migrate deploy
  echo "Prisma migrations completed."

  echo "Running database seeding..."
  npx ts-node --compiler-options '{"module":"commonjs"}' prisma/seed/seed.ts
  echo "Database seeding completed."
else
  echo "Skipping database setup (RUN_MIGRATIONS not set to true)."
fi

python ./scripts/cfg_cron.py &

cmd="$1"
shift
# Prefer virtualenv if set
if [ -n "$VE" ] && [ -x "$VE/bin/$cmd" ]; then
  exec "$VE/bin/$cmd" "$@"
else
  exec "$cmd" "$@"
fi
