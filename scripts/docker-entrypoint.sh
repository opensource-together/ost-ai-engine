#!/bin/sh
set -e

python ./config/cfg.py

echo "Starting database setup..."

echo "Running Prisma migrations..."
npx prisma migrate dev
echo "Prisma migrations completed."

echo "Running database seeding..."
npx ts-node --compiler-options '{"module":"commonjs"}' prisma/seed/seed.ts
echo "Database seeding completed."

python ./scripts/cfg_cron.py &

cmd="$1"
shift
# Prefer virtualenv if set
if [ -n "$VE" ] && [ -x "$VE/bin/$cmd" ]; then
  exec "$VE/bin/$cmd" "$@"
else
  exec "$cmd" "$@"
fi
