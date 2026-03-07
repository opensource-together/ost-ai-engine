#!/bin/bash
set -e

echo "--- Docker disk usage before cleanup ---"
docker system df

echo "\n--- Prune unused images ---"
docker image prune -a -f

echo "\n--- Prune unused volumes ---"
docker volume prune -f

echo "\n--- Prune build cache ---"
docker builder prune -f

echo "\n--- Prune everything (containers, images, volumes, cache) ---"
docker system prune -a --volumes -f

echo "\n--- Docker disk usage after cleanup ---"
docker system df