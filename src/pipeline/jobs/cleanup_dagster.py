import os
import time
import shutil
from pathlib import Path

from dagster import op, job, schedule, RetryPolicy, Backoff, Jitter


@op
def clean_dagster_home(context):
    """
    Clean specific Dagster state directories older than 2 days.

    Targets (relative to $DAGSTER_HOME or default cwd/.dagster_home):
      - history/history
      - logs

    Safety: only removes entries inside those two targets and logs actions.
    """
    dagster_home = os.environ.get("DAGSTER_HOME") or str(Path.cwd() / ".dagster_home")
    root = Path(dagster_home)
    if not root.exists():
        context.log.info(f"dagster home not found: {root} — nothing to clean")
        return {"scanned": 0, "deleted": 0}

    # explicit targets under DAGSTER_HOME
    targets = [root / "history" / "history", root / "logs"]

    # keep items newer than this many days
    days_to_keep = 2
    cutoff = time.time() - (days_to_keep * 24 * 3600)

    scanned = 0
    deleted = 0

    for target in targets:
        if not target.exists():
            context.log.debug(f"cleanup: target does not exist: {target}")
            continue
        # iterate over children and remove those older than cutoff
        for child in target.iterdir():
            try:
                scanned += 1
                mtime = child.stat().st_mtime
                if mtime < cutoff:
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                    deleted += 1
                    context.log.info(f"cleanup: removed {child}")
            except Exception as e:
                context.log.warning(f"cleanup: failed to remove {child}: {e}")

    context.log.info(f"cleanup: scanned={scanned} deleted={deleted} (keeps last {days_to_keep} days)")
    return {"scanned": scanned, "deleted": deleted}



@job()
def cleanup_dagster_history_job():
    clean_dagster_home()


@schedule(cron_schedule="0 3 */3 * *", job_name="cleanup_dagster_history_job")
def cleanup_dagster_history_schedule():
    """Run every 3 days at 03:00 to purge old Dagster history/logs (keep 2 days)."""
    return {}


__all__ = ["cleanup_dagster_history_job", "cleanup_dagster_history_schedule"]
