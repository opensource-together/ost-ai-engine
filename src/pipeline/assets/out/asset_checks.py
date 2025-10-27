"""Cleaned asset checks - scaffold.

Add cleaned-related quality checks here later.
"""

from dagster import (
	asset_check,
	AssetCheckResult,
	MetadataValue,
)

__all__ = []


@asset_check(
	asset="out_github__table_projects_db",
	name="out_github__table_projects_db_counts_valid",
)
def out_github__table_projects_db_counts_valid(context, out_github__table_projects_db):
	"""Validate the DB upsert result contains integer inserted/updated counts >= 0."""
	if not isinstance(out_github__table_projects_db, dict):
		msg = "Output is not a dict/result mapping."
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata={"type": MetadataValue.text(str(type(out_github__table_projects_db)))})

	inserted = out_github__table_projects_db.get("inserted")
	updated = out_github__table_projects_db.get("updated")

	try:
		ok = isinstance(inserted, int) and inserted >= 0 and isinstance(updated, int) and updated >= 0
	except Exception:
		ok = False

	if not ok:
		msg = "Inserted/updated counts are missing or invalid."
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata={"inserted": MetadataValue.text(str(inserted)), "updated": MetadataValue.text(str(updated))})

	return AssetCheckResult(passed=True, description=f"DB upsert counts valid (inserted={inserted}, updated={updated}).", metadata={"inserted": MetadataValue.int(inserted), "updated": MetadataValue.int(updated)})
