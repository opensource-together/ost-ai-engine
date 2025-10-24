#!/bin/sh
set -e

# Run config validator if present
if [ -f ./config/cfg.py ]; then
	python ./config/cfg.py
fi

# Start config cron in background if present (logs to /app/cfg_cron.log)
if [ -f ./scripts/cfg_cron.py ]; then
    nohup python ./scripts/cfg_cron.py >/app/cfg_cron.log 2>&1 &
fi

cmd="$1"
shift
exec "$VE/bin/$cmd" "$@"