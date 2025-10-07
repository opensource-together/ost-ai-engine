import os
import yaml

def load_config():
    with open("src/dagster/config/local.yaml") as f:
        config = yaml.safe_load(f)
"""
Dagster configuration module.
Loads the YAML configuration file and returns it as-is.
Dagster handles environment variable resolution via YAML.
"""
import yaml

def load_config(path="src/dagster/config/local.yaml"):
    """Charge le fichier de configuration YAML pour Dagster."""
    with open(path) as f:
        config = yaml.safe_load(f)
    return config