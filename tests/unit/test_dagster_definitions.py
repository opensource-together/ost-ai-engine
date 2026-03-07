from src.linker.definitions import defs

EXPECTED_ASSET_GROUPS = {
    "ingestion",
    "classification",
    "sync",
    "project_ml",
    "user_ml",
    "default",
}
EXPECTED_JOB_NAMES = {
    "run_all_job",
    "project_enrichment_job",
    "cleanup_dagster_history_job",
    "user_recommendation_job",
}
EXPECTED_SCHEDULE_NAMES = {
    "project_enrichment_job_schedule",
    "cleanup_dagster_history_schedule",
    "user_recommendation_job_schedule",
}
EXPECTED_SENSOR_NAMES: set[str] = set()


class TestDefinitionsLoad:
    def test_defs_object_is_not_none(self) -> None:
        assert defs is not None

    def test_assets_are_registered(self) -> None:
        assets = list(defs.assets or [])
        assert len(assets) > 0

    def test_jobs_are_registered(self) -> None:
        jobs = list(defs.jobs or [])
        actual_names = {j.name for j in jobs}
        assert actual_names == EXPECTED_JOB_NAMES

    def test_schedules_are_registered(self) -> None:
        schedules = list(defs.schedules or [])
        actual_names = {s.name for s in schedules}
        assert actual_names == EXPECTED_SCHEDULE_NAMES

    def test_sensors_are_registered(self) -> None:
        sensors = list(defs.sensors or [])
        actual_names = {s.name for s in sensors}
        assert actual_names == EXPECTED_SENSOR_NAMES


class TestDefinitionsResources:
    def test_required_resources_are_declared(self) -> None:
        resource_defs = defs.resources or {}
        required = {
            "config",
            "fasttext_model",
            "llm_classifier",
            "sentence_transformer",
            "dbt",
            "io_manager",
        }
        for key in required:
            assert key in resource_defs, f"Missing resource: {key}"


class TestDefinitionsAssets:
    def test_key_python_assets_present(self) -> None:
        """Verify critical Python assets are wired into defs."""
        assets = list(defs.assets or [])
        asset_keys = set()
        for a in assets:
            for key in a.keys:
                asset_keys.add(tuple(key.path))

        expected_keys = [
            ("github", "int_github_detection"),
            ("github", "raw_github_project"),
            ("github", "raw_github_readme"),
            ("github", "raw_github_languages"),
            ("github", "raw_github_topics"),
        ]
        for key in expected_keys:
            assert key in asset_keys, f"Missing asset key: {key}"

    def test_dbt_models_asset_present(self) -> None:
        """Verify dbt_models asset is wired."""
        assets = list(defs.assets or [])
        asset_names = set()
        for a in assets:
            if hasattr(a, "op"):
                asset_names.add(a.op.name)
            elif hasattr(a, "node_def"):
                asset_names.add(a.node_def.name)
        assert "dbt_models" in asset_names


class TestJobsResolve:
    def test_all_jobs_resolve_their_asset_selections(self) -> None:
        """Verify every job can resolve its asset selection against defs.

        This catches mismatches between AssetSelection.assets("name")
        and the actual AssetKey registered in Definitions — the exact
        bug that made dagster dev crash before the fix.
        """
        repo = defs.get_repository_def()
        jobs = list(defs.jobs or [])
        for job in jobs:
            resolved = repo.get_job(job.name)
            assert resolved is not None, f"Job {job.name} failed to resolve"
