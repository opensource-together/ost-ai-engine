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
	ins={"core_github__extract_top_projects": AssetIn()},
	group_name="github_projects_scraper",
)
def core_github__table_projects_mapped(context, core_github__extract_top_projects):
	"""Map selected top projects to the Prisma `Project` schema.

	Uses `GITHUB_TO_PROJECT_MAPPING` to populate Prisma fields. Returns mapped list
	and metadata (mapped_count, input_count).
	"""
	if core_github__extract_top_projects is None:
		context.log.warning("No data found from core_github__extract_top_projects. Returning empty list.")
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

	projects = [map_repo(repo) for repo in core_github__extract_top_projects]
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
		"input_count": MetadataValue.int(len(core_github__extract_top_projects)),
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
	description="Map fetched languages to tech_stack and create project_tech_stack relations.",
	ins={"repo_meta": AssetIn("core_github__merge_repo_meta")},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__map_languages_to_techstacks(context, repo_meta: _t.List[_t.Dict]):
	if not repo_meta:
		return Output(value={"mapped": 0})

	mapped = 0
	errors = 0
	def _normalize(s: str) -> str:
		return s.lower().strip().replace("_", " ").replace("-", " ").replace(".", " ")

	with prisma_client() as prisma:
		# use module-level _find_model

		# Try the likely attribute names (match seed/ts usage and prisma-python variants)
		model_ts = _find_model(prisma, ["tech_stack", "TechStack", "techStack", "techstack"])
		if model_ts is None:
			context.log.exception("core_github__map_languages_to_techstacks: TechStack model not found on Prisma client; did you run `prisma generate`?")
			return Output(value={"mapped": 0}, metadata={"mapped": MetadataValue.int(0), "errors": MetadataValue.int(1)})
		try:
			all_ts = model_ts.find_many()
		except Exception as e:
			context.log.exception(f"core_github__map_languages_to_techstacks: failed to load tech_stack rows: {e}")
			return Output(value={"mapped": 0}, metadata={"mapped": MetadataValue.int(0), "errors": MetadataValue.int(1)})

		# Resolve Project and ProjectTechStack models dynamically as well
		project_model = _find_model(prisma, ["project", "Project"]) or _find_model(prisma, ["project_model"])
		if project_model is None:
			context.log.exception("core_github__map_languages_to_techstacks: Project model not found on Prisma client")
			return Output(value={"mapped": 0}, metadata={"mapped": MetadataValue.int(0), "errors": MetadataValue.int(1)})

		pts_model = _find_model(prisma, ["project_tech_stack", "ProjectTechStack", "projectTechStack", "projecttechstack"])
		if pts_model is None:
			context.log.exception("core_github__map_languages_to_techstacks: ProjectTechStack model not found on Prisma client; did you run `prisma generate`?")
			return Output(value={"mapped": 0}, metadata={"mapped": MetadataValue.int(0), "errors": MetadataValue.int(1)})

		ts_map: dict[str, dict] = {}
		for ts in all_ts or []:
			key = _normalize(ts.name)
			ts_map.setdefault(key, []).append(ts)

		# collect small examples of what we matched/created for Dagster metadata
		mapped_examples: list[dict] = []
		unmatched_count = 0
		for item in repo_meta:
			try:
				proj = item.get("project")
				repoUrl = item.get("repoUrl")
				raw_langs = [l for l in (item.get("languages") or []) if isinstance(l, str)]
				if not proj or not raw_langs:
					continue
				# per-repo created counter and matched names list for examples
				repo_created = 0
				repo_matched_names: list[str] = []
				project_rec = project_model.find_first(where={"repoUrl": repoUrl})
				if not project_rec:
					context.log.debug(f"core_github__map_languages_to_techstacks: no project found for repoUrl={repoUrl}")
					continue

				# Normalize and attempt to match each language against seeded tech_stack
				for lang in raw_langs:
					nlang = _normalize(lang)
					matched = []
					# direct normalized match
					if nlang in ts_map:
						matched = ts_map[nlang]
					else:
						# fuzzy-ish: check containment both ways
						for k, ts_list in ts_map.items():
							if nlang in k or k in nlang:
								matched.extend(ts_list)

					# create relations for matched tech stacks only (do NOT create TechStack)
					for ts in matched:
						exists = pts_model.find_first(where={"projectId": project_rec.id, "techStackId": ts.id})
						if not exists:
							pts_model.create(data={"projectId": project_rec.id, "techStackId": ts.id})
							mapped += 1
							repo_created += 1
						# record matched ts name for example output
						repo_matched_names.append(getattr(ts, "name", str(ts.id)))

				# If nothing matched at all, count as unmatched
				if not repo_matched_names:
					unmatched_count += 1

				# capture a small example for metadata (keep first few)
				if len(mapped_examples) < 3:
					mapped_examples.append({
						"repoUrl": repoUrl,
						"input_languages": raw_langs,
						"matched": list(dict.fromkeys(repo_matched_names)),
						"created": repo_created,
					})
			except Exception as e:
				errors += 1
				context.log.exception(
					f"core_github__map_languages_to_techstacks: error processing repoUrl={item.get('repoUrl')} languages={item.get('languages')}: {e}"
				)
				continue

	meta = {"mapped": mapped, "input_count": len(repo_meta), "errors": errors}
	# include small sample examples for debugging in Dagster UI
	meta = {
		"mapped": MetadataValue.int(mapped),
		"unmatched_count": MetadataValue.int(unmatched_count),
		"input_count": MetadataValue.int(len(repo_meta)),
		"errors": MetadataValue.int(errors),
		"sample_mapped": MetadataValue.json(mapped_examples[:3]),
	}
	context.log.info(f"core_github__map_languages_to_techstacks: mapped={mapped} relations across {len(repo_meta)} repos; unmatched={unmatched_count}; sample={ [e.get('repoUrl') for e in mapped_examples[:3]] }")
	return Output(value={"mapped": mapped}, metadata=meta)
