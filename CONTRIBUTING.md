# Contributing — bi-platform

Guide for team members joining the project.

## First-time setup

```bash
# 1. Clone the repo
git clone https://github.com/Pierrafrom/bi-platform.git
cd bi-platform

# 2. Create your .env from the template and fill in Snowflake credentials
cp .env.example .env

# 3. Install Python dependencies (creates .venv automatically)
uv sync

# 4. Install pre-commit hooks (runs checks before every commit)
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# 5. Verify everything works
uv run ruff check airflow/
uv run mypy airflow/
uv run pytest
```

> **IDE**: Install the [ruff VSCode extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
> and enable "Format on Save" — the `.editorconfig` handles indentation automatically.

---

## Branch strategy

```
main  (protected — never push directly)
 └── feat/sprint2/stg-patient       ← your feature branch
 └── feat/sprint2/dag-load-staging
 └── fix/sprint3/null-id-consult
```

- Branch off `main` at the start of each task
- Keep branches short-lived (1–3 days max)
- One PR per logical deliverable — not per sprint

### Branch naming

```
feat/<sprint>/<short-topic>    feat/sprint2/stg-consultation
fix/<sprint>/<short-topic>     fix/sprint2/null-id-patient
refactor/<topic>               refactor/logging-utils
```

---

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add stg_consultation dbt model
fix: handle null ID_TRAITEMENT in int_consultation
test: add unit tests for logging_config
chore: update ruff to 0.11
docs: document dim_patient schema
```

Format: `<type>: <short description in English, imperative mood>`

Types: `feat` · `fix` · `test` · `docs` · `refactor` · `chore` · `ci`

---

## Workflow for a PR

1. Create your branch from `main`
2. Make your changes (pre-commit runs automatically on `git commit`)
3. Push and open a PR — fill in the template
4. Request review from at least 1 teammate
5. CI must be green before merging
6. Squash-merge or regular merge (no force push)

---

## Key commands

```bash
# Python
uv run ruff check airflow/ tests/     # lint
uv run ruff format airflow/ tests/    # format
uv run mypy airflow/                  # type check
uv run pytest                         # tests
uv run pre-commit run --all-files     # run all hooks manually

# dbt (from dbt/ directory)
dbt debug                             # test Snowflake connection
dbt run --select staging              # run staging layer
dbt test --select staging             # test staging layer
dbt run --select +<model>             # model + all upstream
dbt docs generate && dbt docs serve   # lineage browser at localhost:8080
```

---

## Code rules (summary)

- **English** — all identifiers, comments, docstrings
- **Type annotations** — 100 % on all functions, `mypy --strict` must pass
- **No `print()`** — use `logging.getLogger(__name__)`
- **No f-strings in log calls** — use `%s` positional args
- **Single responsibility** — one function does one thing
- **DRY** — extract duplicated logic into a shared helper
- **Google docstrings** — on every public function and class
- **dbt**: `stg_` → `int_` → `fait_` / `dim_` ; always `{{ ref() }}` / `{{ source() }}`

Full details in [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

---

## Questions?

Open a GitHub issue with the label `question`, or ping in the Teams channel.
