# Pipeline Doctor Memory

## Known Fix Patterns

- **IO Manager allowlist**: `_ALLOWED_TABLES` set in `src/linker/resources/io_manager.py` must be updated when new assets/tables are added
- **IO Manager strategy**: Uses truncate-then-append (not `if_exists="replace"` which drops tables)
- **LLM classifier**: Raises exceptions (`ValueError`, `TimeoutError`, `RuntimeError`) instead of returning error dicts. Caller in `core_match__classify_projects.py` catches per-project exceptions via existing try/except
- **LLM client**: Lazy singleton via `PrivateAttr` + `@property` pattern (Dagster `ConfigurableResource` requires this)
- **db.py commit param**: `get_db_connection(commit=)` now properly controls commit vs rollback. When `commit=False` (default), transaction is rolled back on exit
- **Nested try/except swallowing**: In `core_public__sync_projects.py`, used `_CriticalSyncError` custom exception to escape outer except block
- **Subprocess timeouts**: All Go fetcher assets use `timeout=600` on `subprocess.run()`

## Project Conventions

- Python binary is `python3` (not `python`) on this system
- Linter auto-runs on file save and removes unused imports
- `uv` is the package manager (not pip)
