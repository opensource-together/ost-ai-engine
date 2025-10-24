#!/bin/sh
set -e

# Run config validator if present
if [ -f ./config/cfg.py ]; then
	python ./config/cfg.py
fi

# Start config cron in background if present (logs to /app/cfg_cron.log)
if [ -f ./scripts/cfg_cron.py ]; then
    python ./scripts/cfg_cron.py &
fi

cmd="$1"
shift
# Prefer virtualenv if set
if [ -n "$VE" ] && [ -x "$VE/bin/$cmd" ]; then
  exec "$VE/bin/$cmd" "$@"
else
  exec "$cmd" "$@"
fi