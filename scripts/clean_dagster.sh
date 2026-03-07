#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

DAGSTER_HOME_DIR="$PROJECT_ROOT/dagster"

echo "Cleaning directory $DAGSTER_HOME_DIR..."
find "$DAGSTER_HOME_DIR" -mindepth 1 -not -name 'dagster.yaml' -exec rm -rf {} +

echo "Cleanup complete. Only dagster.yaml was preserved."
