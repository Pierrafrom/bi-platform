## Summary
<!-- One sentence: what does this PR do and why? -->

## Sprint / étape
<!-- e.g. Sprint 2 — Étape 2: Ingestion -->

## Changes
<!-- List the main changes. Be specific: model name, DAG name, function name. -->
-
-

## How to test
<!-- How can the reviewer verify this works? -->

## Checklist

### Python (if applicable)

- [ ] `uv run ruff check airflow/ pipeline/ tests/` — no errors
- [ ] `uv run ruff format airflow/ pipeline/ tests/` — no changes
- [ ] `uv run mypy pipeline/` — no errors
- [ ] `uv run pytest` — all tests pass
- [ ] Docstrings on all public functions (Google style)
- [ ] No `print()` — logging used instead

### dbt (if applicable)

- [ ] `dbt compile` passes
- [ ] `dbt run --select <model>` succeeds
- [ ] `dbt test --select <model>` passes
- [ ] `schema.yml` updated with column descriptions and PK tests
- [ ] No hardcoded schema names — `{{ ref() }}` / `{{ source() }}` used

### General

- [ ] CI checks pass (green checkmark on this PR)
- [ ] No credentials, `.env`, or `inputs/` data committed
- [ ] Branch is up-to-date with `main`
