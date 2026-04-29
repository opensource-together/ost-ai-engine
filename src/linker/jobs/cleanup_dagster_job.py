import os
import shutil
import time
from pathlib import Path

from dagster import Field, OpExecutionContext, job, op


def _dagster_home_path() -> Path | None:
    dagster_home = os.environ.get("DAGSTER_HOME", "").strip()
    return Path(dagster_home) if dagster_home else None


def _cleanup_targets(dgh: Path | None) -> list[Path]:
    """Dirs whose children may be pruned by age (`dagster.yaml` layout)."""
    out: list[Path] = []

    logs = os.environ.get("DAGSTER_LOGS_DIR", "").strip()
    if logs:
        out.append(Path(logs))
    elif dgh is not None:
        out.append(dgh / "logs")

    storage = os.environ.get("DAGSTER_STORAGE_DIR", "").strip()
    if storage:
        out.append(Path(storage))
    elif dgh is not None:
        out.append(dgh / "storage")

    if dgh is not None:
        out.append(dgh / ".logs_queue")
        out.append(dgh / "history" / "history")

    seen: set[str] = set()
    unique: list[Path] = []
    for p in out:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


@op(
    config_schema={
        "days_to_keep": Field(
            int,
            default_value=2,
            description="Remove directory entries older than this many days.",
        )
    }
)
def clean_dagster_home(context: OpExecutionContext) -> dict[str, int]:
    """
    Prune Dagster filesystem clutter older than N days.

    Uses ``DAGSTER_LOGS_DIR`` / ``DAGSTER_STORAGE_DIR`` when set
    (see ``dagster.yaml``), else ``$DAGSTER_HOME/logs`` and
    ``$DAGSTER_HOME/storage``. Also ``.logs_queue`` and legacy ``history/history``.
    """
    dgh = _dagster_home_path()
    if dgh is not None and not dgh.exists():
        context.log.info("DAGSTER_HOME missing or invalid path — nothing to clean")
        return {"scanned": 0, "deleted": 0}

    targets = _cleanup_targets(dgh)
    if not targets:
        context.log.info("no Dagster log/storage paths resolved — nothing to clean")
        return {"scanned": 0, "deleted": 0}

    days_to_keep = context.op_config["days_to_keep"]
    cutoff = time.time() - (days_to_keep * 24 * 3600)

    scanned = 0
    deleted = 0

    for target in targets:
        if not target.exists():
            context.log.debug(f"cleanup: target does not exist: {target}")
            continue
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

    context.log.info(
        f"cleanup: scanned={scanned} deleted={deleted} (keeps last {days_to_keep} days)"
    )
    return {"scanned": scanned, "deleted": deleted}


@job()
def cleanup_dagster_history_job() -> None:
    clean_dagster_home()


__all__ = ["cleanup_dagster_history_job"]
