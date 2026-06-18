"""Unit tests for linker bootstrap settings."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.linker.settings import Settings


class TestSettings:
    def test_rejects_missing_dbt_project_dir(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="does not exist"):
            Settings(dbt_project_dir=tmp_path / "missing")

    def test_rejects_file_instead_of_directory(self, tmp_path: Path) -> None:
        file_path = tmp_path / "not-a-dir"
        file_path.write_text("x")
        with pytest.raises(ValidationError, match="not a directory"):
            Settings(dbt_project_dir=file_path)

    def test_rejects_directory_without_dbt_project_yml(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(ValidationError, match="Missing dbt_project.yml"):
            Settings(dbt_project_dir=empty_dir)
