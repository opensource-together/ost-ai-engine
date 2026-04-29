"""Tests for Dagster home cleanup op (paths + env)."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import pytest
from dagster import build_op_context

from src.linker.jobs.cleanup_dagster_job import (
    _cleanup_targets,
    _dagster_home_path,
    clean_dagster_home,
)


def test_cleanup_targets_respects_storage_and_logs_env() -> None:
    with tempfile.TemporaryDirectory() as home:
        dgh = Path(home)
        logs = dgh / "custom_logs"
        storage = dgh / "custom_storage"
        logs.mkdir()
        storage.mkdir()

        os.environ["DAGSTER_LOGS_DIR"] = str(logs)
        os.environ["DAGSTER_STORAGE_DIR"] = str(storage)
        try:
            t = _cleanup_targets(dgh)
            assert logs in t
            assert storage in t
        finally:
            os.environ.pop("DAGSTER_LOGS_DIR", None)
            os.environ.pop("DAGSTER_STORAGE_DIR", None)


def test_cleanup_removes_old_run_dir_under_storage() -> None:
    with tempfile.TemporaryDirectory() as home:
        dgh = Path(home)
        os.environ["DAGSTER_HOME"] = str(dgh)
        storage = dgh / "storage"
        storage.mkdir(parents=True)

        old = storage / "00000000-0000-0000-0000-000000000001"
        old.mkdir()
        old_time = time.time() - (10 * 24 * 3600)
        os.utime(old, (old_time, old_time))

        fresh = storage / "00000000-0000-0000-0000-000000000002"
        fresh.mkdir()

        os.environ["DAGSTER_STORAGE_DIR"] = str(storage)
        try:
            ctx = build_op_context(
                op_config={"days_to_keep": 2},
            )
            result = clean_dagster_home(ctx)
            assert result["deleted"] >= 1
            assert not old.exists()
            assert fresh.exists()
        finally:
            os.environ.pop("DAGSTER_HOME", None)
            os.environ.pop("DAGSTER_STORAGE_DIR", None)


def test_dagster_home_path_empty_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DAGSTER_HOME", raising=False)
    assert _dagster_home_path() is None
