import os
import json
import subprocess
import typing as _t
from contextlib import contextmanager

from dagster import (
    asset,
    AssetIn,
    MetadataValue,
    Output,
)

# Dagster resources
from src.pipeline.resources.cfg_resource import build_scraper_env
from src.pipeline.resources.map.mapping_map import (
    GITLAB_TO_PROJECT_MAPPING,
)

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"go", "github"},
    owners=DEFAULT_OWNERS,
    group_name="github_projects_scraper",
    required_resource_keys={"config"},
)
def raw_github__extract_projects(context):
    """Run the GitHub Go scraper and return scraped projects.

    Description:
    - Executes the compiled Go `github-scraper` binary.
    - Parses stdout as JSON and returns a list of project dicts.
    - Emits metadata: project_count, file_size_bytes, query, preview.
    """
    cfg = context.resources.config
    env = build_scraper_env(cfg)
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w+", delete=True) as tmp_out:
        context.log.info(f"GITHUB_SCRAPING_QUERY to Go: '{env['GITHUB_SCRAPING_QUERY']}'")
        try:
            # Redirect stdout to a temporary file to avoid OOM with large outputs
            with open(tmp_out.name, "w") as f_out:
                result = subprocess.run(
                    ["/app/github-scraper"],
                    stdout=f_out,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd="/app",
                    timeout=120
                )
            
            stderr = (result.stderr or "").strip()
            if result.returncode == 0 and stderr:
                context.log.info(f"GitHub scraper logs:\n{stderr}")
            
            if result.returncode != 0:
                context.log.error(f"GitHub scraper exited with code {result.returncode}")
                context.log.error(f"GitHub scraper stderr: {stderr}")
                # Try to read a bit of the output to see if there's an error message
                tmp_out.seek(0)
                head = tmp_out.read(1000)
                context.log.error(f"GitHub scraper stdout head: {head}")
                raise RuntimeError(f"GitHub scraper failed (exit {result.returncode}). See logs for stderr")

            # Rewind and read the file
            tmp_out.seek(0)
            file_size = os.fstat(tmp_out.fileno()).st_size
            context.log.info(f"Scraper output file size: {file_size} bytes")
            
            if file_size == 0:
                context.log.warning("Scraper output file is empty!")
                return Output(value=[], metadata={"project_count": MetadataValue.int(0), "warning": MetadataValue.text("Empty output file")})

            try:
                parsed = json.load(tmp_out)
            except json.JSONDecodeError as e:
                context.log.error(f"Failed to parse JSON output: {e}")
                tmp_out.seek(0)
                context.log.error(f"Raw output head: {tmp_out.read(500)}")
                raise

            context.log.info(f"Parsed JSON type: {type(parsed)}")
            if isinstance(parsed, dict):
                context.log.info(f"Parsed JSON keys: {list(parsed.keys())}")
                if "items" in parsed:
                    projects = parsed["items"]
                else:
                    context.log.warning("JSON is a dict but missing 'items' key")
                    projects = []
            elif isinstance(parsed, list):
                context.log.info(f"Parsed JSON is a list of length {len(parsed)}")
                projects = parsed
            else:
                context.log.warning(f"Unexpected JSON structure: {type(parsed)}")
                projects = []
            
            count = len(projects)
            context.log.info(f"[DEBUG] github_scraper_asset: {count} projects scraped. Example: {projects[:1]}")
            return Output(
                value=projects,
                metadata={
                    "project_count": MetadataValue.int(count),
                    "file_size_bytes": MetadataValue.int(file_size),
                    "query": MetadataValue.text(env.get("GITHUB_SCRAPING_QUERY", "unknown")),
                    "preview": MetadataValue.json(projects[:1]) if projects else MetadataValue.null(),
                },
            )
        except OSError as e:
            context.log.error(f"GitHub scraper OSError: {e}")
            return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})
        except Exception as e:
            context.log.exception("GitHub scraper error")
            return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})


@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    ins={"raw_github__extract_projects": AssetIn()},
    group_name="github_projects_scraper",
    required_resource_keys={"config"},
)
def raw_github__to_df(context, raw_github__extract_projects: _t.List[_t.Dict]):
    """Convert the raw list-of-dicts into a pandas.DataFrame.

    Provides a single DataFrame that is used as input to
    `core_repo_lang_detect` and `core_repo_primary_language_filter` so they
    can run in parallel on the same dataset.
    """
    # Import pandas directly; let ImportError surface after logging
    try:
        import pandas as pd
    except ImportError as e:
        context.log.error(f"raw_github__to_df: pandas is required but not installed: {e}")
        raise

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
