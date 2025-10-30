"""Staging assets - placeholder package.

Move or implement staging transforms here. For now this module exposes
no assets and acts as a scaffold for future work.
"""
import typing as _t
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
import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
# Lazy-load heavy ML models to avoid importing C extensions at module import
# time which can cause instability when Dagster spawns child processes.
# The actual import is performed in `_load_model`.
from src.pipeline.utils import prisma_client

# fasttext is imported lazily inside the asset that needs it to avoid
# loading its C-extension at module import time (which can cause fork-related
# crashes in a multiprocess executor).

# Globals used by the sentence-transformers based mapping. Initialize here
# to avoid NameError and to make state explicit before any child process
# attempts to access them.
_SENTENCE_MODEL = None
_CATEGORY_EMBS = None
_CATEGORIES = None

__all__ = [
	"core_repo_lang_detect",
	"core_repo_primary_language_filter",
	"raw_github__to_df",
	"core_merge_filtered_projects",
	"core_github__fetch_repo_languages",
	"core_github__fetch_repo_topics",
	"core_github__merge_repo_meta",
	"core_github__map_languages_to_techstacks",
	"core_github__map_topics_to_categories",
]

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
	group_name="github_projects_scraper",
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

	# Lazily import pandas to avoid loading C-extensions at module import time.
	import pandas as pd

	# If a DataFrame is provided, convert to list of dicts for the existing
	# processing logic. If pandas is not available, treat input as list.
	if isinstance(raw_github__df, pd.DataFrame):
		raw_list = raw_github__df.to_dict(orient="records")
	else:
		raw_list = raw_github__df

	cfg = context.resources.config
	model_path = getattr(cfg, "fasttext_model_path", "")

	model = None
	# Import fasttext directly; let ImportError surface if package is missing
	import fasttext
	model = fasttext.load_model(model_path)

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
	group_name="github_projects_scraper",
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
	# Import pandas locally; if missing fail fast with a clear log.
	import pandas as pd

	# Normalize inputs to DataFrames
	def to_df(x):
		if x is None:
			return pd.DataFrame() if pd is not None else []
		if pd is not None and isinstance(x, pd.DataFrame):
			return x
		try:
			return pd.DataFrame(x) if pd is not None else x
		except Exception:
			return pd.DataFrame() if pd is not None else []

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

@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"raw_github__extract_projects": AssetIn()},
	group_name="github_projects_scraper",
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
		# Import pandas directly; let ImportError surface after logging
		import pandas as pd
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
	except ImportError as e:
		context.log.error(f"raw_github__to_df: pandas is required but not installed: {e}")
		raise
	except Exception as e:
		context.log.exception(f"raw_github__to_df: could not convert to DataFrame: {e}")
		# Fallback: return empty DataFrame representation
		try:
			return Output(value=pd.DataFrame(), metadata={"input_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})
		except Exception:
			return Output(value=[], metadata={"input_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description=(
		"Filter repos whose GitHub `language` (primary language) matches a known techstack."
	),
	# Accept the DataFrame produced by `raw_github__to_df` so this asset can run
	# in parallel with `core_repo_lang_detect`.
	ins={"raw_github__df": AssetIn("raw_github__to_df")},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_repo_primary_language_filter(context, raw_github__df: _t.Any):
	"""Keep only repositories whose `language` field (GitHub primary language) matches
	one of the known tech stacks from the project seed file.

	The path to the seed TS file is provided by `context.resources.config.techstacks_seed_path`.
	The function performs a lightweight parse of the TypeScript seed to extract `name` values.
	"""
	seed_path = getattr(context.resources.config, "techstacks_seed_path", "")
	allowed: set[str] = set()
	try:
		p = Path(seed_path)
		# fallback to known json path in the repo if configured path missing
		if not p.exists():
			fallback = Path("prisma/seed/techstacks-data.json")
			if fallback.exists():
				p = fallback
			else:
				context.log.warning(f"techstacks seed file not found at {seed_path} and no fallback found at {fallback}")

		if p.exists():
			# Prefer JSON seed (newer). If JSON, parse and pick LANGUAGE entries when present.
			if p.suffix.lower() == ".json":
				try:
					data = json.loads(p.read_text(encoding="utf-8"))
					names = [d.get("name") for d in data if isinstance(d, dict) and d.get("name")]
					# If `type` is present, prefer only LANGUAGE entries (GitHub primary languages)
					lang_names = [d.get("name") for d in data if isinstance(d, dict) and d.get("type") and d.get("type").upper() == "LANGUAGE"]
					use_names = lang_names if lang_names else names
					allowed = {n.strip().lower() for n in use_names if n and n.strip()}
				except Exception:
					# fallback to regex if json parsing fails
					txt = p.read_text(encoding="utf-8")
					names = re.findall(r"name:\s*[\'\"]([^\'\"]+)[\'\"]", txt)
					allowed = {n.strip().lower() for n in names if n.strip()}
			else:
				# Try to extract from TS/JS using a regex that allows single or double quotes
				txt = p.read_text(encoding="utf-8")
				names = re.findall(r"name:\s*[\'\"]([^\'\"]+)[\'\"]", txt)
				allowed = {n.strip().lower() for n in names if n.strip()}
		else:
			# no seed file available; leave allowed empty and log warning already emitted
			pass
	except Exception as e:
		context.log.warning(f"Could not read techstacks seed file {seed_path}: {e}")

	# Import pandas directly; fail fast if missing
	try:
		import pandas as pd
	except ImportError as e:
		context.log.error(f"core_repo_primary_language_filter: pandas is required but not installed: {e}")
		raise

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



@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"merged_filtered_projects": AssetIn("core_merge_filtered_projects")},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__extract_top_projects(context, merged_filtered_projects):
	"""Select top-N projects with non-empty descriptions, ranked by stars.

	Returns the selected list and metadata (selected_count, input_count, stars_range).
	"""
	top_n = context.resources.config.github_top_n
	# Avoid importing pandas inside the child process: importing pandas/numpy
	# C-extensions in forked processes can trigger SIGBUS/segfaults depending on
	# the environment (BLAS, openmp, etc.). Instead, detect a DataFrame-like
	# object via duck-typing and call `to_dict` if available.
	projects = merged_filtered_projects
	if hasattr(merged_filtered_projects, "to_dict") and callable(getattr(merged_filtered_projects, "to_dict")):
		try:
			projects = merged_filtered_projects.to_dict(orient="records")
		except Exception:
			# If conversion fails, fall back to the original object and handle
			# it below (will warn if it's not a list).
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
	context.log.info(f"[DEBUG] core_github__table_projects_mapped: {len(projects)} mapped projects.")
	return Output(value=projects, metadata={
		"mapped_count": MetadataValue.int(len(projects)),
		"input_count": MetadataValue.int(len(core_github__extract_top_projects)),
	})


# ---- New assets: fetch languages/topics and map to DB relations ----

def _extract_owner_repo(repo_url: str) -> _t.Optional[_t.Tuple[str, str]]:
	try:
		from urllib.parse import urlparse
		p = urlparse(repo_url)
		parts = [seg for seg in p.path.split("/") if seg]
		if len(parts) >= 2:
			return parts[0], parts[1].replace('.git', '')
	except Exception:
		pass
	return None


def _load_model():
	# lazy load global model
	global _SENTENCE_MODEL
	# Return already-loaded model if present
	if _SENTENCE_MODEL is not None:
		return _SENTENCE_MODEL

	# Import sentence-transformers normally inside the loader (fail-fast if missing)
	from sentence_transformers import SentenceTransformer
	_SENTENCE_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
	return _SENTENCE_MODEL


def _load_categories_and_embeddings(seed_json_path: str):
	global _CATEGORY_EMBS, _CATEGORIES
	# Fast fast-path when already computed
	if (_CATEGORY_EMBS is not None) and (_CATEGORIES is not None):
		return _CATEGORIES, _CATEGORY_EMBS
	p = Path(seed_json_path)
	cats = []
	if p.exists():
		try:
			cats = [c.get("name") for c in json.loads(p.read_text(encoding="utf-8")) if c.get("name")]
		except Exception:
			cats = []
	if not cats:
		cats = ["Other"]
	_CATEGORIES = cats
	# Require the sentence-transformers model to be present; fail fast if not.
	texts = [c for c in cats]
	model = _load_model()
	try:
		embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
		_CATEGORY_EMBS = {cats[i]: embs[i] for i in range(len(cats))}
	except Exception as e:
		raise RuntimeError(f"Failed to compute category embeddings: {e}")
	return _CATEGORIES, _CATEGORY_EMBS


def _cosine_sim(a, b) -> float:
	import numpy as np
	return float(np.dot(a, b))


def _map_topics_to_categories(topics: _t.List[str], seed_json_path: str, top_k: int = 2, thresh: float = 0.55) -> _t.List[str]:
	if not topics:
		return []
	# Require model and embeddings to be available; let exceptions propagate so the
	# caller sees a clear error instead of silently proceeding.
	model = _load_model()
	_, cat_embs = _load_categories_and_embeddings(seed_json_path)
	topic_embs = model.encode(topics, convert_to_numpy=True, normalize_embeddings=True)
	matches: set[str] = set()
	for te in topic_embs:
		best = []
		for name, ce in cat_embs.items():
			score = _cosine_sim(te, ce)
			best.append((score, name))
		best.sort(reverse=True, key=lambda x: x[0])
		for score, name in best[:top_k]:
			if score >= thresh:
				matches.add(name)
	return list(matches)


def _fetch_repo_languages_and_topics(owner: str, repo: str, headers: dict, session: requests.Session) -> dict:
    out = {"languages": [], "topics": []}
    try:
        lang_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        topics_url = f"https://api.github.com/repos/{owner}/{repo}/topics"
        r1 = session.get(lang_url, headers=headers, timeout=10)
        if r1.ok:
            out["languages"] = list(r1.json().keys())
    except Exception:
        pass
    try:
        r2 = session.get(topics_url, headers={**headers, "Accept": "application/vnd.github.mercy-preview+json"}, timeout=10)
        if r2.ok:
            json_data = r2.json()
            out["topics"] = json_data.get("names") or json_data.get("topics") or []
    except Exception:
        pass
    return out


def _fetch_repo_languages(owner: str, repo: str, headers: dict, session: requests.Session) -> _t.List[str]:
	out = []
	try:
		lang_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
		r = session.get(lang_url, headers=headers, timeout=10)
		if r.ok:
			out = list(r.json().keys())
	except Exception:
		pass
	return out


def _fetch_repo_topics(owner: str, repo: str, headers: dict, session: requests.Session) -> _t.List[str]:
	out = []
	try:
		topics_url = f"https://api.github.com/repos/{owner}/{repo}/topics"
		r = session.get(topics_url, headers={**headers, "Accept": "application/vnd.github.mercy-preview+json"}, timeout=10)
		if r.ok:
			json_data = r.json()
			out = json_data.get("names") or json_data.get("topics") or []
	except Exception:
		pass
	return out


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description="Fetch GitHub /languages for each project (parallel).",
	ins={"core_github__table_projects_mapped": AssetIn()},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__fetch_repo_languages(context, core_github__table_projects_mapped: _t.List[_t.Dict]):
	if not core_github__table_projects_mapped:
		return Output(value=[], metadata={"count": MetadataValue.int(0)})

	token = getattr(context.resources.config, "github_token", None) or os.environ.get("GITHUB_ACCESS_TOKEN")
	headers = {"Accept": "application/vnd.github.v3+json"}
	if token:
		headers["Authorization"] = f"token {token}"

	results = []
	session = requests.Session()
	max_workers = int(getattr(context.resources.config, "github_fetch_workers", 8))
	with ThreadPoolExecutor(max_workers=max_workers) as ex:
		futures = {}
		for proj in core_github__table_projects_mapped:
			repo_url = proj.get("repoUrl")
			owner_repo = _extract_owner_repo(repo_url) if repo_url else None
			if owner_repo:
				owner, repo = owner_repo
				futures[ex.submit(_fetch_repo_languages, owner, repo, headers, session)] = {"project": proj, "repoUrl": repo_url}
		for fut in as_completed(futures):
			meta = futures[fut]
			try:
				langs = fut.result()
			except Exception as e:
				context.log.warning(f"fetch languages failed: {e}")
				langs = []
			out = {"project": meta["project"], "repoUrl": meta["repoUrl"], "languages": langs}
			results.append(out)
	# include small samples in metadata for debugging
	sample = results[:3]
	sample_repo_urls = [r.get("repoUrl") for r in sample]
	sample_languages = [r.get("languages") for r in sample]
	meta = {
		"count": MetadataValue.int(len(results)),
		"sample": MetadataValue.json(sample),
		"sample_repo_urls": MetadataValue.json(sample_repo_urls),
		"sample_languages": MetadataValue.json(sample_languages),
	}
	return Output(value=results, metadata=meta)


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description="Fetch GitHub /topics for each project (parallel).",
	ins={"core_github__table_projects_mapped": AssetIn()},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__fetch_repo_topics(context, core_github__table_projects_mapped: _t.List[_t.Dict]):
	if not core_github__table_projects_mapped:
		return Output(value=[], metadata={"count": MetadataValue.int(0)})

	token = getattr(context.resources.config, "github_token", None) or os.environ.get("GITHUB_ACCESS_TOKEN")
	headers = {"Accept": "application/vnd.github.v3+json"}
	if token:
		headers["Authorization"] = f"token {token}"

	results = []
	session = requests.Session()
	max_workers = int(getattr(context.resources.config, "github_fetch_workers", 8))
	with ThreadPoolExecutor(max_workers=max_workers) as ex:
		futures = {}
		for proj in core_github__table_projects_mapped:
			repo_url = proj.get("repoUrl")
			owner_repo = _extract_owner_repo(repo_url) if repo_url else None
			if owner_repo:
				owner, repo = owner_repo
				futures[ex.submit(_fetch_repo_topics, owner, repo, headers, session)] = {"project": proj, "repoUrl": repo_url}
		for fut in as_completed(futures):
			meta = futures[fut]
			try:
				topics = fut.result()
			except Exception as e:
				context.log.warning(f"fetch topics failed: {e}")
				topics = []
			out = {"project": meta["project"], "repoUrl": meta["repoUrl"], "topics": topics}
			results.append(out)
	# include small samples in metadata for debugging
	sample = results[:3]
	sample_repo_urls = [r.get("repoUrl") for r in sample]
	sample_topics = [r.get("topics") for r in sample]
	meta = {
		"count": MetadataValue.int(len(results)),
		"sample": MetadataValue.json(sample),
		"sample_repo_urls": MetadataValue.json(sample_repo_urls),
		"sample_topics": MetadataValue.json(sample_topics),
	}
	return Output(value=results, metadata=meta)


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description="Merge languages and topics by repoUrl into a single repo_meta structure.",
	ins={
		"langs": AssetIn("core_github__fetch_repo_languages"),
		"topics": AssetIn("core_github__fetch_repo_topics"),
	},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__merge_repo_meta(context, langs, topics):
	# langs and topics are lists of {project, repoUrl, languages} / {project, repoUrl, topics}
	if not langs and not topics:
		return Output(value=[], metadata={"count": MetadataValue.int(0)})

	by_url = {}
	for item in (langs or []):
		url = item.get("repoUrl")
		if not url:
			continue
		by_url.setdefault(url, {})
		by_url[url].setdefault("project", item.get("project"))
		by_url[url]["languages"] = item.get("languages") or []

	for item in (topics or []):
		url = item.get("repoUrl")
		if not url:
			continue
		by_url.setdefault(url, {})
		# prefer existing project record from langs, else take from topics
		if "project" not in by_url[url]:
			by_url[url]["project"] = item.get("project")
		by_url[url]["topics"] = item.get("topics") or []

	results = []
	for url, data in by_url.items():
		results.append({
			"project": data.get("project"),
			"repoUrl": url,
			"languages": data.get("languages") or [],
			"topics": data.get("topics") or [],
		})

	# include small samples and counts in metadata for easier debugging in the Dagster UI
	sample = results[:3]
	sample_repo_urls = [r.get("repoUrl") for r in sample]
	sample_languages = [r.get("languages") for r in sample]
	sample_topics = [r.get("topics") for r in sample]
	meta = {
		"count": MetadataValue.int(len(results)),
		"sample": MetadataValue.json(sample),
		"sample_repo_urls": MetadataValue.json(sample_repo_urls),
		"sample_languages": MetadataValue.json(sample_languages),
		"sample_topics": MetadataValue.json(sample_topics),
	}
	context.log.info(f"core_github__merge_repo_meta: merged {len(results)} repos; sample_urls={sample_repo_urls}")
	return Output(value=results, metadata=meta)



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
		# Helper: Prisma model attribute name may vary depending on client generation
		def _find_model(client_obj, candidates: list[str]):
			for n in candidates:
				if hasattr(client_obj, n):
					return getattr(client_obj, n)
			return None

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
		"input_count": MetadataValue.int(len(repo_meta)),
		"errors": MetadataValue.int(errors),
		"sample_mapped": MetadataValue.json(mapped_examples[:3]),
	}
	context.log.info(f"core_github__map_languages_to_techstacks: mapped={mapped} relations across {len(repo_meta)} repos; sample={ [e.get('repoUrl') for e in mapped_examples[:3]] }")
	return Output(value={"mapped": mapped}, metadata=meta)


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description="Map fetched topics to categories using sentence-transformers and create project_category relations.",
	ins={"repo_meta": AssetIn("core_github__merge_repo_meta")},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__map_topics_to_categories(context, repo_meta: _t.List[_t.Dict]):
	if not repo_meta:
		return Output(value={"mapped": 0})
	seed_json_path = getattr(context.resources.config, "categories_seed_path", "")
	mapped = 0
	errors = 0
	def _normalize(s: str) -> str:
		return s.strip()

	with prisma_client() as prisma:
		# Helper: Prisma model attribute name may vary depending on client generation
		def _find_model(client_obj, candidates: list[str]):
			for n in candidates:
				if hasattr(client_obj, n):
					return getattr(client_obj, n)
			return None

		# Resolve models we need (Project, Category, ProjectCategory)
		project_model = _find_model(prisma, ["project", "Project"]) or _find_model(prisma, ["project_model"])
		if project_model is None:
			context.log.exception("core_github__map_topics_to_categories: Project model not found on Prisma client")
			return Output(value={"mapped": 0}, metadata={"mapped": MetadataValue.int(0), "errors": MetadataValue.int(1)})

		category_model = _find_model(prisma, ["category", "Category"]) or _find_model(prisma, ["cat", "category_model"])
		if category_model is None:
			context.log.exception("core_github__map_topics_to_categories: Category model not found on Prisma client")
			return Output(value={"mapped": 0}, metadata={"mapped": MetadataValue.int(0), "errors": MetadataValue.int(1)})

		pc_model = _find_model(prisma, ["project_category", "ProjectCategory", "projectCategory", "projectcategory"])
		if pc_model is None:
			context.log.exception("core_github__map_topics_to_categories: ProjectCategory model not found on Prisma client; did you run `prisma generate`?")
			return Output(value={"mapped": 0}, metadata={"mapped": MetadataValue.int(0), "errors": MetadataValue.int(1)})

		# collect small examples for metadata
		mapped_examples: list[dict] = []
		for item in repo_meta:
			try:
				proj = item.get("project")
				repoUrl = item.get("repoUrl")
				topics = [t.replace("-", " ").strip() for t in (item.get("topics") or []) if isinstance(t, str)]
				if not proj or not topics:
					continue
				project_rec = project_model.find_first(where={"repoUrl": repoUrl})
				if not project_rec:
					continue
				matched_category_names = _map_topics_to_categories(topics, seed_json_path, top_k=2, thresh=0.56)
				if not matched_category_names:
					continue

				# Normalize matched names and only keep categories that already exist in DB
				matched_norm = [ _normalize(n) for n in matched_category_names ]
				found = category_model.find_many(where={"name": {"in": matched_norm}})
				# per-repo created counter and matched list for examples
				repo_created = 0
				repo_matched: list[str] = []
				for cat in found or []:
					exists = pc_model.find_first(where={"projectId": project_rec.id, "categoryId": cat.id})
					if not exists:
						pc_model.create(data={"projectId": project_rec.id, "categoryId": cat.id})
						mapped += 1
						repo_created += 1
					# record actual category name from DB (may be normalized)
					repo_matched.append(getattr(cat, "name", str(cat.id)))

				# capture a small example for metadata (keep first few)
				if len(mapped_examples) < 3:
					mapped_examples.append({
						"repoUrl": repoUrl,
						"input_topics": topics,
						"matched": list(dict.fromkeys(repo_matched)),
						"created": repo_created,
					})
			except Exception as e:
				errors += 1
				context.log.exception(f"core_github__map_topics_to_categories: error processing repoUrl={item.get('repoUrl')} topics={item.get('topics')}: {e}")
				continue

	meta = {
		"mapped": MetadataValue.int(mapped),
		"input_count": MetadataValue.int(len(repo_meta)),
		"errors": MetadataValue.int(errors),
		"sample_mapped": MetadataValue.json(mapped_examples[:3]),
	}
	context.log.info(f"core_github__map_topics_to_categories: mapped={mapped} relations across {len(repo_meta)} repos; sample={ [e.get('repoUrl') for e in mapped_examples[:3]] }")
	return Output(value={"mapped": mapped}, metadata=meta)
