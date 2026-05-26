# GitHub Copilot Instructions — bi-platform

NF26 university project (UTC × SMART TEEM).
Stack: **Snowflake · dbt · Apache Airflow · Power BI**.
Domain: hospital data warehouse (patients, consultations, treatments, hospitalisations).

---

## Language

- **All code** (identifiers, comments, docstrings, commit messages): **English**
- **User-facing strings, reports**: French (project audience is French-speaking)
- Source column names in staging SQL keep their French originals (e.g. `ID_PATIENT`, `TS_DEBUT_CONSULT`); rename to English snake_case in intermediate and mart layers

---

## Python (Airflow DAGs and utilities)

### Conventions
- **Python 3.12+** — use modern syntax: `X | Y` unions, `match`, `f`-strings
- **100 % type-annotated** — every function parameter and return value; no `Any` unless unavoidable
- **Google-style docstrings** on every public function, class, and module:
  ```python
  def load_batch(batch_date: date, table: str) -> int:
      """Load a single daily hospital batch into the Snowflake staging layer.

      Args:
          batch_date: Date of the batch folder (e.g. 2026-04-29).
          table: Source table name in uppercase (e.g. "PATIENT").

      Returns:
          Number of rows successfully loaded.

      Raises:
          FileNotFoundError: If the batch folder does not exist.
          SnowflakeLoadError: If the COPY INTO command fails.
      """
  ```
- **Single responsibility** — one function does one thing. If you need "and" to describe it, split it
- **DRY** — extract any logic that appears more than once into a shared helper
- **No bare `except`** — always catch specific exceptions; re-raise or log with context

### Logging
Use the structured logger pattern — never `print()` in production code:

```python
import logging

logger = logging.getLogger(__name__)  # module-level, always __name__

# Levels:
logger.debug("Parsing row %d of %s", row_num, table)       # detailed trace
logger.info("Loaded %d rows into %s.%s", n, schema, table) # normal progress
logger.warning("Null value in column %s at row %d", col, i)# expected anomaly
logger.error("Failed to load %s: %s", table, exc)          # unexpected failure
logger.exception("Unhandled error in DAG %s", dag_id)      # with full traceback
```

- **Never use f-strings in log calls** — use `%s` positional args (ruff rule `G`)
- Logging is configured once at the entry point (DAG / pipeline script), not in library modules
- Each DAG and batch run must log: start time, batch date, rows loaded per table, total duration, any rejected rows

### Structure
```python
# ✅ Good
def extract_batch_path(batch_date: date, table: str) -> Path: ...
def validate_row(row: dict[str, str], schema: TableSchema) -> ValidationResult: ...
def load_to_snowflake(rows: list[dict[str, str]], target: SnowflakeTarget) -> int: ...

# ❌ Avoid
def extract_validate_and_load(date, table, conn): ...
```

### Environment and secrets
- All credentials via **environment variables** (never hardcode)
- Use `python-dotenv` to load `.env` locally; in production use Airflow connections/variables
- Snowflake connection must go through the Airflow `SnowflakeHook`, not raw connector in DAGs

---

## SQL / dbt

### Naming conventions
| Layer | Prefix | Example |
|---|---|---|
| Staging | `stg_` | `stg_patient`, `stg_consultation` |
| Intermediate | `int_` | `int_consultation_enriched` |
| Marts (facts) | `fait_` | `fait_consultation`, `fait_hospitalisation` |
| Marts (dims) | `dim_` | `dim_patient`, `dim_personnel`, `dim_chambre` |

### SQL style
- Keywords **UPPERCASE**: `SELECT`, `FROM`, `WHERE`, `LEFT JOIN`, `GROUP BY`
- One column per line; trailing comma style:
  ```sql
  SELECT
      id_patient,
      nom_patient,
      prenom_patient,
      dt_naiss
  FROM {{ ref('stg_patient') }}
  ```
- **CTEs over subqueries** — name each CTE after what it represents:
  ```sql
  WITH active_patients AS (
      SELECT ...
  ),
  enriched AS (
      SELECT ...
  )
  SELECT * FROM enriched
  ```
- Every model gets a `schema.yml` with `description`, column descriptions, and at minimum `not_null` + `unique` tests on PKs
- Use `{{ source() }}` in staging, `{{ ref() }}` everywhere else — never hardcode schema names

### dbt Jinja / macros
- Extract repeated SQL patterns into macros under `dbt/macros/`
- Document every macro in its `.yml` file

---

## Airflow DAGs

- One DAG per pipeline concern (e.g. `dag_load_staging.py`, `dag_run_dbt.py`)
- Use **TaskFlow API** (`@task` decorator) for Python tasks — not the legacy `PythonOperator`
- Set `doc_md` on every DAG and task for in-UI documentation
- Explicit `depends_on_past=False`, `retries=1`, `retry_delay=timedelta(minutes=5)` as defaults
- DAG IDs: `snake_case`, prefixed by layer — `staging_load_hospital`, `dbt_run_travail`

---

## Architecture reminder

```
inputs/Data Hospital/BDD_HOSPITAL_YYYYMMDD/  (semicolon-delimited .txt, UTF-8)
        │
        ▼ Airflow: dag_load_staging
   Snowflake STAGING  (raw, 1:1 with source, no business logic)
        │
        ▼ Airflow: dag_run_dbt  (dbt run --select intermediate)
   Snowflake TRAVAIL  (quality, unification, dedup)
        │
        ▼ Airflow: dag_run_dbt  (dbt run --select marts)
   Snowflake SOCLE/VUE  (fact + dimension tables)
        │
        ▼ Power BI
```

Source tables: `PATIENT · PERSONNEL · CHAMBRE · MEDICAMENT · CONSULTATION · TRAITEMENT · HOSPITALISATION`
Central join key: `ID_CONSULT` links CONSULTATION → TRAITEMENT → HOSPITALISATION

---

## Key commands

```bash
# Python / linting
uv run ruff check airflow/ pipeline/ tests/     # lint
uv run ruff format airflow/ pipeline/ tests/    # format
uv run mypy pipeline/                           # type check
uv run pytest                                   # tests

# dbt
dbt debug                             # test Snowflake connection
dbt run --select staging              # run staging layer
dbt test --select staging             # test staging layer
dbt docs generate && dbt docs serve   # lineage explorer
```

---

## What NOT to do

- No `print()` — use `logging`
- No hardcoded credentials, schema names, or file paths — use env vars and dbt `ref()`/`source()`
- No `SELECT *` in intermediate or mart models — always explicit columns
- No business logic in staging models — raw ingestion only
- No f-strings in log calls — use `%s` positional formatting
