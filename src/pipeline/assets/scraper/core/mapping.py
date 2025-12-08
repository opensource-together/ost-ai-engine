import typing as _t
from dagster import (
	asset,
	AssetIn,
	MetadataValue,
	Output,
)

from src.pipeline.utils import prisma_client
from .utils import _find_model

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

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
				"topics": item.get("topics") or [],
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
