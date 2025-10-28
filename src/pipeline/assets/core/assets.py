"""Staging assets - placeholder package.

Move or implement staging transforms here. For now this module exposes
no assets and acts as a scaffold for future work.
"""
import typing as _t
import pandas as pd
from pathlib import Path
import re
from collections import Counter

from dagster import (
	asset,
	AssetIn,
	MetadataValue,
	Output,
)
from src.pipeline.resources.map.mapping_map import (
    GITHUB_TO_PROJECT_MAPPING,
)

try:
	import fasttext
except Exception:  # pragma: no cover - runtime environment may not have fasttext
	fasttext = None

# Keep the same owners convention as other assets
DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description=(
		"Detect repo language using fastText; annotate with `language` and "
		"`language_confidence`, and filter non‑Latin/scripted languages."
	),
	# Accept the DataFrame produced by `raw_github__to_df` so this asset can run
	# in parallel with `core_repo_primary_language_filter`.
	ins={"raw_github__df": AssetIn("raw_github__to_df")},
	required_resource_keys={"config"},
)
def core_repo_lang_detect(context, raw_github__df: _t.Any):
	"""Annotate repos with detected language and filter non-Latin/scripted languages.

	Output: list of repo dicts with `language` and `language_confidence` added.
	Fallback: if fastText/model missing -> pass-through (logs error).
	"""
	# Accept either a DataFrame (from the new transformer asset) or the
	# original list-of-dicts. Be permissive for backwards compatibility.
	if raw_github__df is None:
		context.log.info("core_repo_lang_detect: no input projects, returning empty list")
		return Output(value=[], metadata={"input_count": MetadataValue.int(0)})

	# If a DataFrame is provided, convert to list of dicts for the existing
	# processing logic.
	if isinstance(raw_github__df, pd.DataFrame):
		raw_list = raw_github__df.to_dict(orient="records")
	else:
		raw_list = raw_github__df

	cfg = context.resources.config
	model_path = getattr(cfg, "fasttext_model_path", "/app/models/lid.176.ftz")

	model = None
	if fasttext is None:
		context.log.error("fasttext package not installed; core_repo_lang_detect will pass through data unchanged.")
	else:
		try:
			model = fasttext.load_model(model_path)
		except Exception as e:
			context.log.error(f"Could not load fastText model at {model_path}: {e}")
			model = None

	# Blacklist of language codes using non-Latin scripts or languages the pipeline
	# should exclude (Arabic, CJK, Japanese, Korean, many Indic languages...)
	NON_LATIN_LANGS = {
		"ar", "zh", "ja", "ko",
		"hi", "bn", "ta", "te", "kn", "ml", "gu", "mr", "pa", "or", "si", "ne", "my",
	}

	accepted: _t.List[_t.Dict] = []
	filtered_out = 0

	for i, repo in enumerate(raw_list):
		# Build text to detect language from several possible fields
		text_parts = []
		for key in ("combined_text", "readme", "description", "name"):
			v = repo.get(key)
			if isinstance(v, str) and v.strip():
				text_parts.append(v.strip())
		text = "\n".join(text_parts)[:20000]

		if not text:
			repo["language"] = None
			repo["language_confidence"] = 0.0
			accepted.append(repo)
			continue

		lang_code = None
		confidence = 0.0
		if model is not None:
			try:
				labels, probs = model.predict(text.replace("\n", " "), k=1)
				if labels:
					# fastText labels are like '__label__en'
					lang_code = labels[0].replace("__label__", "")
					confidence = float(probs[0]) if probs else 0.0
			except Exception as e:
					context.log.warning(f"fastText prediction failed for repo index {i}: {e}")

		repo["language"] = lang_code
		repo["language_confidence"] = confidence

		if lang_code and lang_code in NON_LATIN_LANGS:
			filtered_out += 1
			context.log.debug(f"core_repo_lang_detect: filtering out repo [{repo.get('name')}] detected as {lang_code} (conf={confidence:.3f})")
			continue

		accepted.append(repo)

	# Build helpful metadata for debugging
	lang_counts: dict = {}
	for r in accepted:
		k = r.get("language") or "<none>"
		lang_counts[k] = lang_counts.get(k, 0) + 1

	sample = accepted[:3]
	meta = {
		"input_count": MetadataValue.int(len(raw_list)),
		"output_count": MetadataValue.int(len(accepted)),
		"filtered_out": MetadataValue.int(filtered_out),
		"sample": MetadataValue.json(sample),
		"language_counts": MetadataValue.json(lang_counts),
	}
	context.log.info(f"core_repo_lang_detect: kept {len(accepted)} / {len(raw_list)} projects (filtered_out={filtered_out}); sample={sample}")
	# Return a list of dicts to remain compatible with existing asset checks
	return Output(value=accepted, metadata=meta)



@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"core_repo_lang_detect": AssetIn(), "core_repo_primary_language_filter": AssetIn()},
	required_resource_keys={"config"},
)
def core_merge_filtered_projects(context, core_repo_lang_detect, core_repo_primary_language_filter):
	"""Merge the two filtered outputs produced in parallel.

	Default behavior: perform an inner join on `id` (GitHub numeric id). If `id`
	is not present in both dataframes, fall back to `full_name`, `html_url`, or
	`name` (in that order) if available in both.

	The merge is an intersection: only repos kept by both filters remain. This
	follows the semantics "remove rows each asset must remove".
	"""
	# Normalize inputs to DataFrames
	def to_df(x):
		if x is None:
			return pd.DataFrame()
		if isinstance(x, pd.DataFrame):
			return x
		try:
			return pd.DataFrame(x)
		except Exception:
			return pd.DataFrame()

	df1 = to_df(core_repo_lang_detect)
	df2 = to_df(core_repo_primary_language_filter)

	# Choose join key
	common_keys = ["id", "full_name", "html_url", "name"]
	join_key = None
	for k in common_keys:
		if k in df1.columns and k in df2.columns:
			join_key = k
			break

	if join_key is None:
		context.log.warning("core_merge_filtered_projects: no common join key found; returning lang-detect output as fallback")
		merged = df1
	else:
		try:
			merged = pd.merge(df1, df2[[join_key]], on=join_key, how="inner")
			context.log.info(f"core_merge_filtered_projects: merged on '{join_key}', resulting rows={len(merged)}")
		except Exception as e:
			context.log.exception(f"core_merge_filtered_projects: merge failed: {e}")
			merged = df1

	records = merged.to_dict(orient="records")
	meta = {
		"left_count": MetadataValue.int(len(df1)),
		"right_count": MetadataValue.int(len(df2)),
		"merged_count": MetadataValue.int(len(records)),
		"join_key": MetadataValue.text(join_key or "none"),
		"sample": MetadataValue.json(records[:3]),
		"sample_ids": MetadataValue.json([r.get(join_key) for r in records[:3]]) if join_key else MetadataValue.json([]),
	}
	return Output(value=records, metadata=meta)


__all__ = [
	"core_repo_lang_detect",
	"core_repo_primary_language_filter",
	"raw_github__to_df",
	"core_merge_filtered_projects",
]


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"raw_github__extract_projects": AssetIn()},
	required_resource_keys={"config"},
)
def raw_github__to_df(context, raw_github__extract_projects: _t.List[_t.Dict]):
	"""Convert the raw list-of-dicts into a pandas.DataFrame.

	This asset provides a single DataFrame that is used as input to
	`core_repo_lang_detect` and `core_repo_primary_language_filter` so they
	can run in parallel on the same dataset.
	"""
	if not raw_github__extract_projects:
		context.log.info("raw_github__to_df: no input projects, returning empty DataFrame")
		df = pd.DataFrame()
		return Output(value=df, metadata={"input_count": MetadataValue.int(0)})

	try:
		df = pd.DataFrame(raw_github__extract_projects)
		sample_records = df.head(3).to_dict(orient="records")
		sample_ids = [r.get("id") for r in sample_records]
		meta = {
			"input_count": MetadataValue.int(len(df)),
			"columns_count": MetadataValue.int(len(df.columns)),
			"sample": MetadataValue.json(sample_records),
			"sample_ids": MetadataValue.json(sample_ids),
		}
		context.log.info(f"raw_github__to_df: converted {len(df)} projects to DataFrame; columns={list(df.columns)[:6]}")
		return Output(value=df, metadata=meta)
	except Exception as e:
		context.log.exception(f"raw_github__to_df: could not convert to DataFrame: {e}")
		# Fallback: return empty DataFrame
		return Output(value=pd.DataFrame(), metadata={"input_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description=(
		"Filter repos whose GitHub `language` (primary language) matches a known techstack."
	),
	# Accept the DataFrame produced by `raw_github__to_df` so this asset can run
	# in parallel with `core_repo_lang_detect`.
	ins={"raw_github__df": AssetIn("raw_github__to_df")},
	required_resource_keys={"config"},
)
def core_repo_primary_language_filter(context, raw_github__df: _t.Any):
	"""Keep only repositories whose `language` field (GitHub primary language) matches
	one of the known tech stacks from the project seed file.

	The path to the seed TS file is provided by `context.resources.config.techstacks_seed_path`.
	The function performs a lightweight parse of the TypeScript seed to extract `name` values.
	"""
	seed_path = getattr(context.resources.config, "techstacks_seed_path", "/app/prisma/seed/techstacks-data.ts")
	allowed: set[str] = set()
	try:
		p = Path(seed_path)
		if p.exists():
			txt = p.read_text(encoding="utf-8")
			names = re.findall(r"name:\s*'([^']+)'", txt)
			allowed = {n.strip().lower() for n in names if n.strip()}
		else:
			context.log.warning(f"techstacks seed file not found at {seed_path}")
	except Exception as e:
		context.log.warning(f"Could not read techstacks seed file {seed_path}: {e}")

	try:
		# Accept DataFrame or list-of-dicts
		if isinstance(raw_github__df, pd.DataFrame):
			raw_list = raw_github__df.to_dict(orient="records")
		else:
			raw_list = raw_github__df or []

		kept = []
		filtered_count = 0
		for i, repo in enumerate(raw_list):
			lang = repo.get("language")
			if isinstance(lang, str) and lang.strip() and lang.strip().lower() in allowed:
				kept.append(repo)
			else:
				filtered_count += 1

		# Build metadata
		sample_kept = kept[:3]
		allowed_sample = list(sorted(allowed))[:10]
		meta = {
			"input_count": MetadataValue.int(len(raw_list)),
			"kept_count": MetadataValue.int(len(kept)),
			"filtered_out": MetadataValue.int(filtered_count),
			"allowed_count": MetadataValue.int(len(allowed)),
			"allowed_sample": MetadataValue.json(allowed_sample),
			"sample": MetadataValue.json(sample_kept),
		}
		context.log.info(f"core_repo_primary_language_filter: kept {len(kept)} / {len(raw_list)} projects; allowed_count={len(allowed)}; sample={sample_kept}")
		# Return DataFrame for downstream merging
		try:
			df = pd.DataFrame(kept)
			return Output(value=df, metadata=meta)
		except Exception:
			return Output(value=kept, metadata=meta)
	except Exception as e:
		# Catch any unexpected errors to avoid crashing the dagster child process
		context.log.exception(f"core_repo_primary_language_filter: unexpected error: {e}")
		return Output(value=[], metadata={
			"input_count": MetadataValue.int(0),
			"error": MetadataValue.text(str(e)),
		})


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"merged_filtered_projects": AssetIn("core_merge_filtered_projects")},
	required_resource_keys={"config"},
)
def core_github__extract_top_projects(context, merged_filtered_projects):
	"""Select top-N projects with non-empty descriptions, ranked by stars.

	Returns the selected list and metadata (selected_count, input_count, stars_range).
	"""
	top_n = context.resources.config.github_top_n
	# Accept DataFrame or list-of-dicts
	if isinstance(merged_filtered_projects, pd.DataFrame):
		projects = merged_filtered_projects.to_dict(orient="records")
	else:
		projects = merged_filtered_projects

	if not projects or not isinstance(projects, list):
		context.log.warning("No projects to rank.")
		return []

	filtered = [p for p in projects if p.get("description") not in (None, "")]
	context.log.info(f"[DEBUG] core_github__extract_top_projects: {len(filtered)} projects with description out of {len(projects)}")
	if not filtered:
		context.log.warning("[DEBUG] core_github__extract_top_projects: No project with description found.")
		return Output(value=[], metadata={
			"selected_count": MetadataValue.int(0),
			"reason": MetadataValue.text("No project with description found."),
		})
	ranked = sorted(filtered, key=lambda p: p.get("stargazers_count", 0), reverse=True)
	top_projects = ranked[:top_n]
	meta = {
		"selected_count": MetadataValue.int(len(top_projects)),
		"input_count": MetadataValue.int(len(projects)),
		"stars_range": MetadataValue.text(f"{top_projects[0].get('stargazers_count', 0)} - {top_projects[-1].get('stargazers_count', 0)}") if top_projects else MetadataValue.null(),
	}
	return Output(value=top_projects, metadata=meta)


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"core_github__extract_top_projects": AssetIn()},
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
	context.log.info(f"[DEBUG] core_github__table_projects_mapped: {len(projects)} mapped projects.")
	return Output(value=projects, metadata={
		"mapped_count": MetadataValue.int(len(projects)),
		"input_count": MetadataValue.int(len(core_github__extract_top_projects)),
	})
