#!/bin/bash
set -e

# Chemin absolu du dossier contenant main.go
GITHUB_SCRAPER_DIR="/Users/hich/Desktop/git.nosync/ost-linker/src/services/go/scraper"
GITHUB_OUTPUT_BIN="/Users/hich/Desktop/git.nosync/ost-linker/data/github-scraper"

# Compilation
echo "Compiling GitHub Scraper..."
cd "$GITHUB_SCRAPER_DIR"
go build -o "$GITHUB_OUTPUT_BIN" main.go

echo "Binaire généré : $GITHUB_OUTPUT_BIN"