import os
import json
import subprocess
import typing as _t
from dagster import (
    asset,
    MetadataValue,
    Output,
)
from src.pipeline.resources.cfg_resource import build_scraper_env

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"go", "github"},
    owners=DEFAULT_OWNERS,
    group_name="ingestion",
    required_resource_keys={"config"},
)
def raw_github__extract_projects(context):
    """
    Executes the external Go scraper to fetch GitHub project data.
    """
    context.log.info("raw_github__extract_projects: Starting GitHub scraper execution")
    cfg = context.resources.config
    env = build_scraper_env(cfg)
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w+", delete=True) as tmp_out:
        context.log.info(f"GITHUB_SCRAPING_QUERY to Go: '{env['GITHUB_SCRAPING_QUERY']}'")
        try:
            # Redirect stdout to a temporary file
            scraper_path = os.environ.get("GO_SCRAPER_PATH", "/app/github-scraper")
            with open(tmp_out.name, "w") as f_out:
                result = subprocess.run(
                    [scraper_path],
                    stdout=f_out,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd=os.getcwd(),
                    timeout=120
                )
            
            stderr = (result.stderr or "").strip()
            if result.returncode == 0 and stderr:
                context.log.info(f"GitHub scraper logs:\n{stderr}")
            
            if result.returncode != 0:
                context.log.error(f"GitHub scraper exited with code {result.returncode}")
                context.log.error(f"GitHub scraper stderr: {stderr}")
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
            projects = []
            if isinstance(parsed, dict):
                if "items" in parsed:
                    projects = parsed["items"]
                else:
                    context.log.warning("JSON is a dict but missing 'items' key")
            elif isinstance(parsed, list):
                projects = parsed
            else:
                context.log.warning(f"Unexpected JSON structure: {type(parsed)}")
            
            count = len(projects)
            context.log.info(f"[DEBUG] github_scraper_asset: {count} projects scraped.")
            return Output(
                value=projects,
                metadata={
                    "project_count": MetadataValue.int(count),
                    "file_size_bytes": MetadataValue.int(file_size),
                    "query": MetadataValue.text(env.get("GITHUB_SCRAPING_QUERY", "unknown")),
                },
            )
        except OSError as e:
            context.log.error(f"GitHub scraper OSError: {e}")
            return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})
        except Exception as e:
            context.log.exception("GitHub scraper error")
            return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})
