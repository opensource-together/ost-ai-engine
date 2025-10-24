#!/bin/sh
set -e

python ./config/cfg.py

python ./scripts/cfg_cron.py &

cmd="$1"
shift
# Prefer virtualenv if set
if [ -n "$VE" ] && [ -x "$VE/bin/$cmd" ]; then
  exec "$VE/bin/$cmd" "$@"
else
  exec "$cmd" "$@"
fi
