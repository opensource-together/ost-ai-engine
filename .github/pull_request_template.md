## Summary

<!-- What this PR does. Link related issues with "Closes #123". -->

## Changes

<!-- Key changes. -->

-

## Checklist

- [ ] **`make ci-check`** passes locally (ruff, format, mypy, unit tests, Dagster smoke)
- [ ] If you changed `dbt/`: `make ci-check-full` (needs `DATABASE_URL`) or rely on CI `dbt-build` / sqlfluff
- [ ] Commits are atomic and follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] PR targets **`develop`** (not `main` or `staging`)
