from dagster import asset

@asset
def hello_asset():
	"""Un asset de base pour Dagster."""
	return "Hello Dagster!"
