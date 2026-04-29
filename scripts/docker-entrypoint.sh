#!/bin/bash
# Start as root so we can chown Docker named volumes (mounted with root ownership)
# before dropping to appuser (uid 1000). Compose uses volumes for dagster_home
# and dbt/target.
set -e
if [[ "$(id -u)" == "0" ]]; then
  mkdir -p \
    "${DAGSTER_HOME:-/app/dagster_home}/storage" \
    "${DAGSTER_HOME:-/app/dagster_home}/logs" \
    /app/dbt/target \
    /app/.cache/huggingface \
    /app/.cache/sentence-transformers
  chown -R appuser:appuser \
    "${DAGSTER_HOME:-/app/dagster_home}" \
    /app/dbt/target \
    /app/.cache 2>/dev/null || true
  exec gosu appuser "$@"
fi
exec "$@"
