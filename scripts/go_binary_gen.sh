#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GITHUB_SCRAPER_DIR="$PROJECT_ROOT/src/services/go/scraper"
GITHUB_OUTPUT_BIN="$PROJECT_ROOT/data/github-scraper"

# Compilation
echo "Compiling GitHub Scraper..."
cd "$GITHUB_SCRAPER_DIR"
go build -o "$GITHUB_OUTPUT_BIN" main.go

echo "Binary generated: $GITHUB_OUTPUT_BIN"

# Trending Scraper
GITHUB_TRENDING_DIR="$PROJECT_ROOT/src/services/go/trending"
GITHUB_TRENDING_BIN="$PROJECT_ROOT/data/ost-trending"
echo "Compiling GitHub Trending Scraper..."
cd "$GITHUB_TRENDING_DIR"
go build -o "$GITHUB_TRENDING_BIN" .
echo "Binary generated: $GITHUB_TRENDING_BIN"
