import typing as _t
from pathlib import Path
import re
import json
from dagster import (
	asset,
	AssetIn,
	MetadataValue,
	Output,
)

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
	required_resource_keys={"config", "fasttext_model"},
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

	# Get the fastText model from Dagster resources (loaded once, reused across runs)
	fasttext_resource = context.resources.fasttext_model
	model = fasttext_resource.model

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
