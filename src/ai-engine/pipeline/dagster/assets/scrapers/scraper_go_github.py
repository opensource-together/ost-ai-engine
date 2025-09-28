from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from dagster import asset


@asset(name="scraper_go_github", group_name="ost_scrapers")
def scrape_github_projects(context) -> None:
    repo_root = Path(__file__).resolve().parents[6]
    binary = repo_root / "src" / "infrastructure" / "services" / "go" / "github" / "scraper"
    if not binary.exists():
        context.log.warn("GitHub scraper binary not found. Skipping execution.")
        return

    env = os.environ.copy()

    context.log.info("Starting GitHub scraper binary: %s", str(binary))
    start_ts = time.monotonic()

    with subprocess.Popen(
        [str(binary)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        bufsize=1,
    ) as proc:
        assert proc.stdout is not None
        for line in proc.stdout:
            context.log.info(line.rstrip("\n"))
        return_code = proc.wait()

    elapsed_s = time.monotonic() - start_ts
    if return_code != 0:
        context.log.error("GitHub scraper failed (code=%s) in %.2fs", return_code, elapsed_s)
        raise RuntimeError(f"GitHub scraper failed with exit code {return_code}")
    context.log.info("GitHub scraper completed in %.2fs", elapsed_s)



