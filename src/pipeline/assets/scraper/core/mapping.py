import typing as _t
from dagster import (
	asset,
	AssetIn,
	MetadataValue,
	Output,
)
from src.pipeline.resources.map.mapping_map import (
    GITHUB_TO_PROJECT_MAPPING,
)
from src.pipeline.utils import prisma_client
from .utils import _find_model

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"core_github__merge_filtered_projects": AssetIn()},
	group_name="github_projects_scraper",
)
def core_github__table_projects_mapped(context, core_github__merge_filtered_projects):
	"""Map selected top projects to the Prisma `Project` schema.

	Uses `GITHUB_TO_PROJECT_MAPPING` to populate Prisma fields. Returns mapped list
	and metadata (mapped_count, input_count).
	"""
	if core_github__merge_filtered_projects is None:
		context.log.warning("No data found from core_github__merge_filtered_projects. Returning empty list.")
		return []

	def map_repo(repo):
		mapped = {}
		for prisma_field, source in GITHUB_TO_PROJECT_MAPPING.items():
			if callable(source):
				mapped[prisma_field] = source(repo)
			elif isinstance(source, str) and "." in source:
				keys = source.split(".")
				value = repo
				for k in keys:
					value = value.get(k, None) if isinstance(value, dict) else None
				mapped[prisma_field] = value
			elif isinstance(source, str):
				mapped[prisma_field] = repo.get(source)
			else:
				mapped[prisma_field] = source
		return mapped

	projects = [map_repo(repo) for repo in core_github__merge_filtered_projects]
	# Build enriched metadata for Dagster UI: include small previews and mapping keys
	def _preview_text(s: str, limit: int = 1000) -> str:
		if not s:
			return ""
		try:
			if len(s) <= limit:
				return s
			return s[:limit] + "..."
		except Exception:
			return ""

	mapped_examples: list[dict] = []
	for p in projects[:3]:
		try:
			mapped_preview = {k: p.get(k) for k in list(p.keys())[:12]}
			mapped_examples.append({
				"repoUrl": p.get("repoUrl"),
				"name": p.get("name"),
				"description": _preview_text(p.get("description") or "", limit=500),
				"mapped_preview": mapped_preview,
			})
		except Exception:
			mapped_examples.append({"repoUrl": p.get("repoUrl"), "error": "preview_failed"})

	mapping_keys = list(GITHUB_TO_PROJECT_MAPPING.keys())

	meta = {
		"mapped_count": MetadataValue.int(len(projects)),
		"input_count": MetadataValue.int(len(core_github__merge_filtered_projects)),
		"sample": MetadataValue.json(projects[:3]),
		"sample_repo_urls": MetadataValue.json([p.get("repoUrl") for p in projects[:3]]),
		"mapping_keys": MetadataValue.json(mapping_keys),
		"sample_mapped": MetadataValue.json(mapped_examples),
	}
	context.log.info(f"core_github__table_projects_mapped: mapped={len(projects)} projects; sample_urls={ [p.get('repoUrl') for p in projects[:3]] }; mapping_keys={mapping_keys[:6] }")
	return Output(value=projects, metadata=meta)



@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"repo_meta": AssetIn("core_github__merge_repo_meta")},
	group_name="map_repos_metadatas",
	required_resource_keys={"config"},
)
def core_github__enrich_project_data(context, repo_meta: _t.List[_t.Dict]):
	"""
	Enriches project data by mapping languages to TechStacks.

	**Description:**
	Maps detected languages to existing TechStack records in the database to establish relationships.

	**Logic:**
	1. **Fetch TechStacks**: Retrieves all TechStack records from the database.
	2. **Normalization**: Normalizes language names and TechStack names for matching.
	3. **Mapping**: Matches languages to TechStacks using exact and fuzzy matching.
	4. **Structure**: Prepares the data with `tech_stack_ids` for the database upsert.

	**Output:**
	List of enriched project dictionaries ready for database insertion.
	"""
	context.log.info(f"core_github__enrich_project_data: Starting with {len(repo_meta) if repo_meta else 0} input items")
	if not repo_meta:
		return Output(value=[], metadata={"count": MetadataValue.int(0)})

	def _normalize(s: str) -> str:
		return s.lower().strip().replace("_", " ").replace("-", " ").replace(".", " ")

	with prisma_client() as prisma:
		if prisma is None:
			context.log.error("core_github__enrich_project_data: Prisma client unavailable.")
			return Output(value=[], metadata={"error": MetadataValue.text("Prisma client unavailable")})

		# Fetch TechStacks
		model_ts = _find_model(prisma, ["tech_stack", "TechStack", "techStack", "techstack"])
		ts_map = {}
		if model_ts:
			try:
				all_ts = model_ts.find_many()
				for ts in all_ts:
					key = _normalize(ts.name)
					ts_map.setdefault(key, []).append(ts)
				context.log.info(f"Loaded {len(all_ts)} TechStacks for mapping.")
			except Exception as e:
				context.log.warning(f"Failed to fetch TechStacks: {e}")
		else:
			context.log.error("TechStack model not found in Prisma client.")

		# ProjectTechStack model (added by user instruction)
		pts_model = _find_model(prisma, ["project_tech_stack", "ProjectTechStack", "projectTechStack", "projecttechstack"])
		if not pts_model:
			context.log.error("ProjectTechStack model not found in Prisma client.")

		results = []
		for item in repo_meta:
			project_data = item.get("project") or {}
			repo_url = item.get("repoUrl")
			
			# Map Languages -> TechStacks
			raw_langs = item.get("languages") or []
			matched_ts_ids = set()
			for lang in raw_langs:
				if not isinstance(lang, str): continue
				nlang = _normalize(lang)
				if nlang in ts_map:
					for ts in ts_map[nlang]:
						matched_ts_ids.add(ts.id)
				else:
					# fuzzy check
					for k, ts_list in ts_map.items():
						if nlang in k or k in nlang:
							for ts in ts_list:
								matched_ts_ids.add(ts.id)

			# Structure for upsert
			# We pass the original project data plus the lists of IDs to connect
			enriched_item = {
				"project": project_data,
				"repoUrl": repo_url,
				"readme": item.get("readme"),
				"tech_stack_ids": list(matched_ts_ids),
			}
			results.append(enriched_item)
			
			if len(results) <= 3:
				context.log.info(f"Sample enriched item: {repo_url} -> matched {len(matched_ts_ids)} tech stacks: {list(matched_ts_ids)}")

	# Metadata
	sample = results[:3]
	meta = {
		"count": MetadataValue.int(len(results)),
		"sample": MetadataValue.json(sample),
	}
	context.log.info(f"core_github__enrich_project_data: Enriched {len(results)} projects.")
	return Output(value=results, metadata=meta)
