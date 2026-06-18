#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"
mkdir -p "$DATA_DIR"

GITHUB_SCRAPER_DIR="$PROJECT_ROOT/src/services/go/scraper"
GITHUB_OUTPUT_BIN="$DATA_DIR/github-scraper"

echo "Compiling GitHub Scraper..."
cd "$GITHUB_SCRAPER_DIR"
go build -o "$GITHUB_OUTPUT_BIN" main.go
echo "Binary generated: $GITHUB_OUTPUT_BIN"

FETCHER_DIR="$PROJECT_ROOT/src/services/go/fetcher"
FETCHER_BIN="$DATA_DIR/ost-fetcher"
echo "Compiling GitHub Fetcher..."
cd "$FETCHER_DIR"
go build -o "$FETCHER_BIN" .
echo "Binary generated: $FETCHER_BIN"

GITHUB_TRENDING_DIR="$PROJECT_ROOT/src/services/go/trending"
GITHUB_TRENDING_BIN="$DATA_DIR/ost-trending"
echo "Compiling GitHub Trending Scraper..."
cd "$GITHUB_TRENDING_DIR"
go build -o "$GITHUB_TRENDING_BIN" .
echo "Binary generated: $GITHUB_TRENDING_BIN"
