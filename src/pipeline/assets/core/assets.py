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
# Lazy-load heavy ML models to avoid importing C extensions at module import time which can cause instability when Dagster spawns child processes.
from src.pipeline.utils import prisma_client

# Globals used by the sentence-transformers based mapping. Initialize here to avoid NameError and to make state explicit before any child process
_SENTENCE_MODEL = None
_CATEGORY_EMBS = None
_CATEGORIES = None


# Generic helper: resolve a model attribute on the Prisma client using common
# candidate names (snake_case, camelCase, PascalCase). Returns the model
# object or None.
def _find_model(client_obj, candidates: list[str]):
	for n in candidates:
		if hasattr(client_obj, n):
			return getattr(client_obj, n)
	return None


# Helper to compute embeddings for Category rows fetched from the DB.
# Returns (cat_objs, cat_embs) where cat_embs is a numpy array with one
# embedding per category in the same order as cat_objs.
def _get_db_category_embeddings(category_model, context):
	all_categories = category_model.find_many()
	cat_objs = list(all_categories or [])
	if not cat_objs:
		return [], None, None
	try:
		model = _load_model()
		cat_texts = [getattr(c, "name", "") for c in cat_objs]
		cat_embs = model.encode(cat_texts, convert_to_numpy=True, normalize_embeddings=True)
		return cat_objs, cat_embs, model
	except Exception as e:
		context.log.exception(f"_get_db_category_embeddings: failed to load model/compute embeddings: {e}")
		return cat_objs, None, None

__all__ = [
	"core_repo_lang_detect",
	"core_repo_primary_language_filter",
	"raw_github__to_df",
	"core_merge_filtered_projects",
	"core_github__fetch_repo_languages",
	"core_github__fetch_repo_topics",
	"core_github__merge_repo_meta",
	"core_github__normalize_repo_meta",
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

	Behaviour changes:
	- If any non‑Latin/scripted language is detected (even as a minority),
	  the repo is filtered out.
	- We check both textual script presence (CJK, Arabic, Devanagari, etc.)
	  and fastText's top-k predictions to catch mixed languages like
	  "chinese + english".
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

	# Regex to detect non-Latin script characters directly in text (CJK, Arabic, Devanagari, Bengali, Tamil, Hangul, etc.)
	NON_LATIN_CHAR_RE = re.compile(
		r"[\u4E00-\u9FFF"  # CJK Unified Ideographs
		r"\u3040-\u30FF"   # Hiragana + Katakana
		r"\uAC00-\uD7AF"   # Hangul
		r"\u0590-\u05FF"   # Hebrew
		r"\u0600-\u06FF"   # Arabic
		r"\u0900-\u097F"   # Devanagari
		r"\u0980-\u09FF"   # Bengali
		r"\u0B80-\u0BFF"   # Tamil
		r"\u0C00-\u0C7F"   # Telugu
		r"\u0C80-\u0CFF"   # Kannada
		r"\u0D00-\u0D7F"   # Malayalam
		r"]"
	)

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

		# Default annotations
		repo["language"] = None
		repo["language_confidence"] = 0.0

		# If text contains non-Latin script characters -> immediate filter
		if text and NON_LATIN_CHAR_RE.search(text):
			# No need to run fastText; annotate language_confidence as 1.0 for reporting
			repo["language"] = None
			repo["language_confidence"] = 1.0
			filtered_out += 1
			context.log.debug(f"core_repo_lang_detect: filtering out repo [{repo.get('name')}] because non-Latin script characters were found in text")
			continue

		# If no text to analyze, keep but with null language
		if not text:
			accepted.append(repo)
			continue

		# Use fastText top-k predictions and treat any presence of blacklisted code
		# (even as a minority) as reason to filter.
		lang_code = None
		confidence = 0.0
		try:
			# request top-3 labels to catch mixed-language predictions
			labels, probs = model.predict(text.replace("\n", " "), k=3)
			# Ensure we have plain Python iterables (avoid numpy array truth checks)
			labels_list = list(labels) if labels is not None else []
			probs_list = list(probs) if probs is not None else []
			# labels like '__label__en' or bytes; normalize safely
			preds = []
			for lb, pr in zip(labels_list, probs_list):
				# decode bytes if sentence-transformers/fasttext returns bytes
				if isinstance(lb, bytes):
					try:
						lb = lb.decode("utf-8")
					except Exception:
						lb = str(lb)
				if isinstance(lb, str):
					code = lb.replace("__label__", "").strip()
					try:
						pr_val = float(pr)
					# some predictors may return non-float types; fallback to 0.0
					except Exception:
						pr_val = 0.0
					preds.append((code, pr_val))
			# choose top for primary annotation
			if preds:
				lang_code, confidence = preds[0]
			# if any predicted code is blacklisted (even with small prob), filter out
			blacklisted = any((c in NON_LATIN_LANGS) for c, _ in preds)
			if blacklisted:
				repo["language"] = lang_code
				repo["language_confidence"] = confidence
				filtered_out += 1
				context.log.debug(f"core_repo_lang_detect: filtering out repo [{repo.get('name')}] because fastText top-k includes non-Latin code among {preds}")
				continue
		except Exception as e:
			# If fastText fails, log and keep (do not filter) to avoid dropping data silently.
			context.log.warning(f"fastText prediction failed for repo index {i}: {e}")

		# If we reach here, no non-Latin indication found -> annotate and accept
		repo["language"] = lang_code
		repo["language_confidence"] = confidence
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
		"filtered_out_percent": MetadataValue.float(round(100 * filtered_out / len(raw_list), 2) if raw_list else 0.0),
		"sample": MetadataValue.json(sample),
		"language_counts": MetadataValue.json(lang_counts),
	}
	context.log.info(f"core_repo_lang_detect: kept {len(accepted)} / {len(raw_list)} projects (filtered {filtered_out} = {meta['filtered_out_percent']}%); top languages={dict(sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5])}")
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
	"""Select projects with non-empty descriptions. Do not sort or limit by stars."""
	# Avoid importing pandas inside the child process; use duck-typing to convert if needed.
	projects = merged_filtered_projects
	if hasattr(merged_filtered_projects, "to_dict") and callable(getattr(merged_filtered_projects, "to_dict")):
		try:
			projects = merged_filtered_projects.to_dict(orient="records")
		except Exception:
			projects = merged_filtered_projects

	if not projects or not isinstance(projects, list):
		context.log.warning("No projects to select.")
		return Output(value=[], metadata={"selected_count": MetadataValue.int(0), "input_count": MetadataValue.int(0)})

	# Keep all projects that have a non-empty description (no sorting or top-N selection).
	filtered = [p for p in projects if p.get("description") not in (None, "")]
	context.log.info(f"core_github__extract_top_projects: {len(filtered)} projects with description out of {len(projects)}")

	if not filtered:
		return Output(value=[], metadata={
			"selected_count": MetadataValue.int(0),
			"input_count": MetadataValue.int(len(projects)),
			"reason": MetadataValue.text("No project with description found."),
		})

	meta = {
		"selected_count": MetadataValue.int(len(filtered)),
		"input_count": MetadataValue.int(len(projects)),
	}
	return Output(value=filtered, metadata=meta)


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
	# Import numpy lazily to avoid loading its C extensions at module import
	# time which can cause SIGBUS when using a multiprocess/fork executor.
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
	description="Fetch GitHub README for each project (parallel).",
	ins={"core_github__table_projects_mapped": AssetIn()},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__fetch_readme(context, core_github__table_projects_mapped: _t.List[_t.Dict]):
	if not core_github__table_projects_mapped:
		return Output(value=[], metadata={"count": MetadataValue.int(0)})

	token = getattr(context.resources.config, "github_token", None) or os.environ.get("GITHUB_ACCESS_TOKEN")
	headers = {"Accept": "application/vnd.github.v3+json"}
	if token:
		headers["Authorization"] = f"token {token}"

	results = []
	session = requests.Session()
	max_workers = int(getattr(context.resources.config, "github_fetch_workers", 8))
	# Limit the number of concurrent threads to reduce contention on Dagster's
	# SQLite event log (concurrent thread logging can cause sqlite locking
	# errors). Keep at least 1 worker but cap to a conservative value.
	max_workers = max(1, min(max_workers, 4))
	with ThreadPoolExecutor(max_workers=max_workers) as ex:
		futures = {}
		for proj in core_github__table_projects_mapped:
			repo_url = proj.get("repoUrl")
			owner_repo = _extract_owner_repo(repo_url) if repo_url else None
			if owner_repo:
				owner, repo = owner_repo
				futures[ex.submit(_fetch_readme, owner, repo, headers, session)] = {"project": proj, "repoUrl": repo_url}
		for fut in as_completed(futures):
			meta = futures[fut]
			try:
				readme = fut.result()
			except Exception as e:
				context.log.warning(f"fetch readme failed: {e}")
				readme = ""
			out = {"project": meta["project"], "repoUrl": meta["repoUrl"], "readme": readme}
			results.append(out)

	sample = results[:3]
	sample_repo_urls = [r.get("repoUrl") for r in sample]
	meta = {
		"count": MetadataValue.int(len(results)),
		"sample": MetadataValue.json(sample),
		"sample_repo_urls": MetadataValue.json(sample_repo_urls),
	}
	return Output(value=results, metadata=meta)


def _fetch_readme(owner: str, repo: str, headers: dict, session: requests.Session) -> str:
	out = ""
	try:
		readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
		# Prefer raw content when possible
		r = session.get(readme_url, headers={**headers, "Accept": "application/vnd.github.v3.raw"}, timeout=10)
		if r.ok:
			out = r.text
		else:
			# fallback to JSON which may contain base64 encoded content
			r2 = session.get(readme_url, headers=headers, timeout=10)
			if r2.ok:
				try:
					j = r2.json()
					content = j.get("content")
					encoding = j.get("encoding")
					if content and encoding == "base64":
						import base64

						out = base64.b64decode(content.encode("utf-8")).decode("utf-8", errors="ignore")
				except Exception:
					out = ""
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
	# Cap concurrency to avoid SQLite locking in Dagster's event log.
	max_workers = max(1, min(max_workers, 4))
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
	# Cap concurrency to avoid SQLite locking in Dagster's event log.
	max_workers = max(1, min(max_workers, 4))
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
	description="Merge languages, topics and readme by repoUrl into a single repo_meta structure.",
	ins={
		"langs": AssetIn("core_github__fetch_repo_languages"),
		"topics": AssetIn("core_github__fetch_repo_topics"),
		"readmes": AssetIn("core_github__fetch_readme"),
	},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__merge_repo_meta(context, langs, topics, readmes):
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
		# also preserve any description present on the mapped project dict
		try:
			proj = by_url[url].get("project") or {}
			if isinstance(proj, dict):
				desc = proj.get("description")
				if desc:
					by_url[url]["description"] = desc
		except Exception:
			pass

	for item in (topics or []):
		url = item.get("repoUrl")
		if not url:
			continue
		by_url.setdefault(url, {})
		# prefer existing project record from langs, else take from topics
		if "project" not in by_url[url]:
			by_url[url]["project"] = item.get("project")
		by_url[url]["topics"] = item.get("topics") or []

	# incorporate readme fetch results (separate asset)
	for item in (readmes or []):
		url = item.get("repoUrl")
		if not url:
			continue
		by_url.setdefault(url, {})
		# attach raw readme text for use in embeddings/context
		by_url[url]["readme"] = item.get("readme") or ""

	results = []
	for url, data in by_url.items():
		results.append({
			"project": data.get("project"),
			"repoUrl": url,
			"languages": data.get("languages") or [],
			"topics": data.get("topics") or [],
			"description": data.get("description") or (data.get("project") or {}).get("description"),
			"readme": data.get("readme") or (data.get("project") or {}).get("readme"),
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
	description="Normalize description/readme text for embedding (lowercase + strip punctuation).",
	ins={"repo_meta": AssetIn("core_github__merge_repo_meta")},
	group_name="github_projects_scraper",
	required_resource_keys={"config"},
)
def core_github__normalize_repo_meta(context, repo_meta: _t.List[_t.Dict]):
	"""Produce a normalized version of repo_meta suitable for embeddings.

	Adds fields to each item: `clean_description`, `clean_readme`, `clean_context`.
	`clean_context` is a concatenation of cleaned description/readme and a few
	project fields, truncated to a safe length.
	"""
	if not repo_meta:
		return Output(value=[], metadata={"count": MetadataValue.int(0)})

	def _clean_text_for_embedding(s: str, max_len: int = 8000) -> str:
		if not s:
			return ""
		# Lowercase
		s = s.lower()
		# Remove punctuation (keep alphanumerics and whitespace)
		s = re.sub(r"[^0-9a-z\s]", " ", s)
		# Collapse whitespace
		s = re.sub(r"\s+", " ", s).strip()
		# Truncate
		if len(s) > max_len:
			return s[:max_len] + "..."
		return s

	out = []
	for item in repo_meta:
		try:
			proj = item.get("project") or {}
			desc = item.get("description") or (proj.get("description") if isinstance(proj, dict) else None)
			readme = item.get("readme") or (proj.get("readme") if isinstance(proj, dict) else None)
			# Build a combined context then clean
			parts = []
			if isinstance(desc, str) and desc.strip():
				parts.append(desc.strip())
			if isinstance(readme, str) and readme.strip():
				parts.append(readme.strip())
			# Also include small textual fields from mapped project if present
			if isinstance(proj, dict):
				for k in ("combined_text", "readme", "description", "name"):
					v = proj.get(k)
					if isinstance(v, str) and v.strip():
						parts.append(v.strip())
			context_text = "\n".join(parts).strip()
			clean_desc = _clean_text_for_embedding(desc or "")
			clean_readme = _clean_text_for_embedding(readme or "")
			clean_context = _clean_text_for_embedding(context_text or "")
			new_item = dict(item)
			new_item["clean_description"] = clean_desc
			new_item["clean_readme"] = clean_readme
			new_item["clean_context"] = clean_context
			out.append(new_item)
		except Exception as e:
			context.log.exception(f"core_github__normalize_repo_meta: failed for repo {item.get('repoUrl')}: {e}")
			# still append original item to maintain pipeline shape
			out.append(item)

	# small metadata sample
	sample = out[:3]
	meta = {
		"count": MetadataValue.int(len(out)),
		"sample": MetadataValue.json(sample),
		"sample_repo_urls": MetadataValue.json([r.get("repoUrl") for r in sample]),
	}
	return Output(value=out, metadata=meta)



@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description="Map fetched languages to tech_stack and create project_tech_stack relations.",
	ins={"repo_meta": AssetIn("core_github__normalize_repo_meta")},
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


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	description="Map fetched topics to categories using sentence-transformers and create project_category relations.",
	ins={"repo_meta": AssetIn("core_github__normalize_repo_meta")},
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
		# Normalize to lowercase and replace common separators to improve matching
		return s.lower().strip().replace("_", " ").replace("-", " ").replace(".", " ")

	with prisma_client() as prisma:
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

		# Preload categories and compute embeddings from DB names (helper)
		cat_objs, cat_embs, model = _get_db_category_embeddings(category_model, context)
		if not cat_objs or cat_embs is None or model is None:
			context.log.info("core_github__map_topics_to_categories: no category embeddings available; nothing to map.")
			return Output(value={"mapped": 0}, metadata={"mapped": MetadataValue.int(0), "errors": MetadataValue.int(0)})

		# collect small examples for metadata
		mapped_examples: list[dict] = []
		unmatched_count = 0
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

				# Compute topic embeddings and compare against DB category embeddings
				try:

					# Topics embeddings: incorporate pre-cleaned context produced by
					# `core_github__normalize_repo_meta` when available (clean_context).
					# This avoids duplicating cleaning logic here and ensures a single
					# normalized text source across the pipeline.
					# encode topics
					topic_embs = model.encode(topics, convert_to_numpy=True, normalize_embeddings=True)
					if hasattr(topic_embs, "ndim") and topic_embs.ndim == 1:
						# single topic -> make it 2D
						topic_embs = topic_embs.reshape(1, -1)

					# encode pre-cleaned context text if present
					ctx_vec = None
					try:
						clean_ctx = item.get("clean_context") or ""
						if isinstance(clean_ctx, str) and clean_ctx.strip():
							ctx_emb = model.encode([clean_ctx], convert_to_numpy=True, normalize_embeddings=True)
							if hasattr(ctx_emb, "ndim"):
								if ctx_emb.ndim == 2:
									ctx_vec = ctx_emb[0]
								elif ctx_emb.ndim == 1:
									ctx_vec = ctx_emb
					except Exception as e:
						context.log.debug(f"core_github__map_topics_to_categories: failed to encode clean_context for repoUrl={repoUrl}: {e}")

					# aggregate topic embeddings (and optional context) to get a
					# single vector representing the repo topics+context
					# Import numpy locally to avoid loading C-extensions at
					# module import time (prevent SIGBUS in forked children).
					import numpy as np
					if ctx_vec is not None:
						try:
							topic_vec = np.mean(np.vstack([topic_embs, ctx_vec]), axis=0)
						except Exception:
							topic_vec = topic_embs.mean(axis=0)
					else:
						topic_vec = topic_embs.mean(axis=0)

					# compute similarities to each category embedding
					scores = np.dot(cat_embs, topic_vec)
					best_idx = int(np.argmax(scores))
					best_score = float(scores[best_idx])
					# threshold to avoid spurious matches
					THRESH = float(getattr(context.resources.config, "categories_match_thresh", 0.56))
					match_mode = None
					if best_score >= THRESH:
						# confident embedding match
						found = [cat_objs[best_idx]]
						match_mode = "embedding"
					else:
						# fallback: try simple text-token heuristics between topics and category names
						# prepare normalized category texts
						cat_texts = [getattr(c, "name", "") for c in cat_objs]
						cat_norms = [ _normalize(t) for t in cat_texts ]
						topics_norm = [ _normalize(t) for t in topics ]
						best_fallback_idx = None
						best_overlap = 0
						for ti, tnorm in enumerate(topics_norm):
							for ci, cnorm in enumerate(cat_norms):
								# direct containment (topic in category name or vice versa)
								if tnorm and (tnorm in cnorm or cnorm in tnorm):
									best_fallback_idx = ci
									best_overlap = max(best_overlap, 1)
									continue
								# word overlap
								tokens_t = set([w for w in re.split(r"\s+", tnorm) if w])
								tokens_c = set([w for w in re.split(r"\s+", cnorm) if w])
								overlap = len(tokens_t & tokens_c)
								if overlap > best_overlap:
									best_overlap = overlap
									best_fallback_idx = ci
						if best_fallback_idx is not None and best_overlap > 0:
							found = [cat_objs[best_fallback_idx]]
							match_mode = "text_fallback"
						else:
							found = []
				except Exception as e:
					context.log.exception(f"core_github__map_topics_to_categories: failed to compute topic embeddings or similarity for repoUrl={repoUrl}: {e}")
					found = []
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

				# If nothing matched at all, count as unmatched
				if not found:
					unmatched_count += 1

				# capture a small example for metadata (keep first few)
				if len(mapped_examples) < 3:
					# Include short previews of description/readme in the sample so the
					# Dagster UI can show context for why a category was chosen. We keep
					# previews reasonably sized to avoid bloating the metadata UI.
					def _preview_text(s: str, limit: int = 2000) -> str:
						if not s:
							return ""
						try:
							if len(s) <= limit:
								return s
							return s[:limit] + "..."
						except Exception:
							return ""

					proj_desc = None
					proj_readme = None
					# mapped_project may not be defined in this scope if we relied on
					# the centralized clean_context; ensure we read from item.project
					mapped_project = item.get("project") or {}
					try:
						proj_desc = item.get("description") or (mapped_project or {}).get("description")
						proj_readme = item.get("readme") or (mapped_project or {}).get("readme")
					except Exception:
						proj_desc = None
						proj_readme = None

					mapped_examples.append({
						"repoUrl": repoUrl,
						"input_topics": topics,
						"matched": list(dict.fromkeys(repo_matched)),
						"created": repo_created,
						"score": float(best_score) if 'best_score' in locals() else None,
						"description": _preview_text(proj_desc) if isinstance(proj_desc, str) else None,
						"readme": _preview_text(proj_readme) if isinstance(proj_readme, str) else None,
					})
			except Exception as e:
				errors += 1
				context.log.exception(f"core_github__map_topics_to_categories: error processing repoUrl={item.get('repoUrl')} topics={item.get('topics')}: {e}")
				continue

	meta = {
		"mapped": MetadataValue.int(mapped),
		"unmatched_count": MetadataValue.int(unmatched_count),
		"input_count": MetadataValue.int(len(repo_meta)),
		"errors": MetadataValue.int(errors),
		"sample_mapped": MetadataValue.json(mapped_examples[:3]),
	}
	context.log.info(f"core_github__map_topics_to_categories: mapped={mapped} relations across {len(repo_meta)} repos; unmatched={unmatched_count}; sample={ [e.get('repoUrl') for e in mapped_examples[:3]] }")
	return Output(value={"mapped": mapped}, metadata=meta)
