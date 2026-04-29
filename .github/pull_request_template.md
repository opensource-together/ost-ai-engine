## Summary

<!-- What does this PR do? Link related issues with "Closes #123". -->

## Changes

<!-- List the key changes made in this PR. -->

-

## Checklist

- [ ] **`make ci-check`** passes (matches GitHub Actions Python quality job: ruff, format, mypy, unit + API + Dagster smoke — see [CONTRIBUTING.md](../CONTRIBUTING.md))
- [ ] If you changed `dbt/`: `cd dbt && uv run dbt parse` (and `dbt test` when you have a matching DB)
- [ ] Commits are atomic and follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] PR targets **`staging`** (not `main`)
