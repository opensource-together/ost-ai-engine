"""Staging assets - placeholder package.

Move or implement staging transforms here. For now this module exposes
no assets and acts as a scaffold for future work.
"""
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
	ins={"raw_github__extract_projects": AssetIn()},
	required_resource_keys={"config"},
)
def core_repo_lang_detect(context, raw_github__extract_projects: _t.List[_t.Dict]):
	"""Annotate repos with detected language and filter non-Latin/scripted languages.

	Output: list of repo dicts with `language` and `language_confidence` added.
	Fallback: if fastText/model missing -> pass-through (logs error).
	"""
	if not raw_github__extract_projects:
		context.log.info("core_repo_lang_detect: no input projects, returning empty list")
		return []

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

	for i, repo in enumerate(raw_github__extract_projects):
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

	meta = {
		"input_count": MetadataValue.int(len(raw_github__extract_projects)),
		"output_count": MetadataValue.int(len(accepted)),
		"filtered_out": MetadataValue.int(filtered_out),
	}
	context.log.info(f"core_repo_lang_detect: kept {len(accepted)} / {len(raw_github__extract_projects)} projects (filtered_out={filtered_out})")
	return Output(value=accepted, metadata=meta)


__all__ = ["core_repo_lang_detect"]


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"core_repo_lang_detect": AssetIn()},
    required_resource_keys={"config"},
)
def core_github__extract_top_projects(context, core_repo_lang_detect):
	"""Select top-N projects with non-empty descriptions, ranked by stars.

	Returns the selected list and metadata (selected_count, input_count, stars_range).
	"""
	top_n = context.resources.config.github_top_n
	if not core_repo_lang_detect or not isinstance(core_repo_lang_detect, list):
		context.log.warning("No projects to rank.")
		return []
	filtered = [p for p in core_repo_lang_detect if p.get("description") not in (None, "")]
	context.log.info(f"[DEBUG] core_github__extract_top_projects: {len(filtered)} projects with description out of {len(core_repo_lang_detect)}")
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
		"input_count": MetadataValue.int(len(core_repo_lang_detect)),
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
