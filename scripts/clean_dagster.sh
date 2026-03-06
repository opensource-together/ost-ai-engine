#!/bin/bash

# Définir le chemin du dossier .dagster_home
HOME="/Users/hich/Desktop/git.nosync/ost-linker"
DAGSTER_HOME_DIR="$HOME/dagster"

echo "Nettoyage du dossier $DAGSTER_HOME_DIR..."
find "$DAGSTER_HOME_DIR" -mindepth 1 -not -name 'dagster.yaml' -exec rm -rf {} +

echo "Nettoyage terminé. Seul le fichier dagster.yaml a été conservé."