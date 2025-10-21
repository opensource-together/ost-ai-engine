#!/bin/sh
set -e

python ./config/cfg.py

exec "$@"
