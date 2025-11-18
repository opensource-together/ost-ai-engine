from dagster import define_asset_job, AssetSelection

# Placeholder jobs focused on future embedding asset groups.
# These jobs currently select groups that do not yet contain assets.
# Once assets are added with group_name matching the group keys below,
# these jobs will run those assets.

projects_embedding_job = define_asset_job(
    name="projects_embedding_job",
    selection=AssetSelection.groups("projects_embedding"),
)

categories_embedding_job = define_asset_job(
    name="categories_embedding_job",
    selection=AssetSelection.groups("categories_embedding"),
)

users_embedding_job = define_asset_job(
    name="users_embedding_job",
    selection=AssetSelection.groups("users_embedding"),
)
