import typing as _t
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dagster import (
	asset,
	AssetIn,
	MetadataValue,
	Output,
)
from .utils import (
    _extract_owner_repo,
    _fetch_readme,
    _fetch_repo_languages,
    _fetch_repo_topics,
)

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"core_github__table_projects_mapped": AssetIn()},
	group_name="fetch_projects_metadatas",
	required_resource_keys={"config"},
)
def core_github__fetch_readme(context, core_github__table_projects_mapped: _t.List[_t.Dict]):
	"""
	Fetch GitHub README for each project (parallel).

	**Description:**
	Retrieves the README content for each mapped project to be used for embedding generation.

	**Logic:**
	1. **Setup**: Configures GitHub token and thread pool.
	2. **Parallel Fetching**: Submits requests to GitHub API for each project.
	3. **Error Handling**: Captures failures and returns empty string for missing READMEs.

	**Output:**
	List of dictionaries containing project metadata and README content.
	"""
	context.log.info(f"core_github__fetch_readme: Starting fetch for {len(core_github__table_projects_mapped) if core_github__table_projects_mapped else 0} projects")
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
			# Truncate readme to avoid OOM/SIGBUS on large files (limit to 50KB)
			if len(readme) > 50000:
				readme = readme[:50000]
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


@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"core_github__table_projects_mapped": AssetIn()},
	group_name="fetch_projects_metadatas",
	required_resource_keys={"config"},
)
def core_github__fetch_repo_languages(context, core_github__table_projects_mapped: _t.List[_t.Dict]):
	"""
	Fetch GitHub /languages for each project (parallel).

	**Description:**
	Retrieves the language breakdown for each project from GitHub API.

	**Logic:**
	1. **Setup**: Configures GitHub token and thread pool.
	2. **Parallel Fetching**: Submits requests to GitHub API `languages` endpoint.
	3. **Error Handling**: Returns empty list on failure.

	**Output:**
	List of dictionaries containing project metadata and list of languages.
	"""
	context.log.info(f"core_github__fetch_repo_languages: Starting fetch for {len(core_github__table_projects_mapped) if core_github__table_projects_mapped else 0} projects")
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
	ins={"core_github__table_projects_mapped": AssetIn()},
	group_name="fetch_projects_metadatas",
	required_resource_keys={"config"},
)
def core_github__fetch_repo_topics(context, core_github__table_projects_mapped: _t.List[_t.Dict]):
	"""
	Fetch GitHub /topics for each project (parallel).

	**Description:**
	Retrieves the repository topics (tags) for each project from GitHub API.

	**Logic:**
	1. **Setup**: Configures GitHub token and thread pool.
	2. **Parallel Fetching**: Submits requests to GitHub API `topics` endpoint (mercy-preview).
	3. **Error Handling**: Returns empty list on failure.

	**Output:**
	List of dictionaries containing project metadata and list of topics.
	"""
	context.log.info(f"core_github__fetch_repo_topics: Starting fetch for {len(core_github__table_projects_mapped) if core_github__table_projects_mapped else 0} projects")
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
	ins={
		"langs": AssetIn("core_github__fetch_repo_languages"),
		"topics": AssetIn("core_github__fetch_repo_topics"),
		"readmes": AssetIn("core_github__fetch_readme"),
	},
	group_name="fetch_projects_metadatas",
	required_resource_keys={"config"},
)
def core_github__merge_repo_meta(context, langs, topics, readmes):
	"""
	Merge languages, topics and readme by repoUrl into a single repo_meta structure.

	**Description:**
	Aggregates the results from parallel metadata fetching steps into a single unified structure per repository.

	**Logic:**
	1. **Aggregation**: Iterates through languages, topics, and readmes results.
	2. **Indexing**: Groups data by `repoUrl`.
	3. **Merging**: Combines all metadata fields into a single dictionary for each project.

	**Output:**
	List of fully enriched repository metadata dictionaries.
	"""
	# langs and topics are lists of {project, repoUrl, languages} / {project, repoUrl, topics}
	context.log.info(f"core_github__merge_repo_meta: Merging metadata (langs={len(langs) if langs else 0}, topics={len(topics) if topics else 0}, readmes={len(readmes) if readmes else 0})")
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
