# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

NF26 university project at UTC, supervised by SMART TEEM (data consulting firm).
Goal: build a full BI decision-support platform — a Snowflake Data Warehouse fed from flat files, transformed with dbt, orchestrated by Airflow, and visualized in Power BI.

The source data models a **hospital** (patients, staff, rooms, consultations, treatments, hospitalisations, medications).

This is a greenfield repo. Code is written incrementally across 4 sprints (21/05 → 18/06/2026). Do not anticipate deliverables from future sprints — work strictly from what has been defined for the current sprint.

---

## Tech stack

| Tool | Role |
|---|---|
| Snowflake | Cloud DWH — all SQL layers live here |
| dbt | SQL transformations (Staging → Travail → Socle/Vue) |
| Apache Airflow | DAG orchestration of the transformation chain |
| Power BI | Final reporting and dashboards |
| GitLab | Version control and CI/CD |

---

## Architecture

Data flows from flat files → Snowflake (3 layers) → Power BI:

```
inputs/Data Hospital/BDD_HOSPITAL_YYYYMMDD/
    │   (7 semicolon-delimited .txt files, one batch per day)
    ▼
┌─────────────────────────────────────────────────┐
│                  Snowflake                       │
│                                                  │
│  Staging/ODS  →  Travail  →  Socle/Vue          │
│  (contrôle /     (qualité     (historisation)    │
│   rejet)          unification)                   │
└─────────────────────────────────────────────────┘
         dbt (transformations)
         Airflow (orchestration)
                                    │
                                    ▼
                                Power BI
```

**Layer responsibilities:**
- **Staging/ODS**: Raw ingestion, quality control, rejection management
- **Travail**: Quality unification, deduplication, business rules
- **Socle/Vue**: Historized fact and dimension tables (star/snowflake schema) for Power BI

---

## Source data

### File format

- Location: `inputs/Data Hospital/BDD_HOSPITAL_YYYYMMDD/TABLE_YYYYMMDD.txt`
- Delimiter: **semicolon (`;`)**
- Encoding: UTF-8
- One folder per day; currently 12 daily batches (29/04/2026 → 10/05/2026)
- Reference files: `inputs/Hopital CI VF.xlsx` (data quality rules), `inputs/Hopital Mapping VF.xlsx` (source→target column mapping)

### Tables and columns

**PATIENT** — master patient record
```
ID_PATIENT ; NOM_PATIENT ; PRENOM_PATIENT ; DT_NAISS ; VILLE_NAISS ; PAYS_NAISS
NUM_SECU ; IND_PAYS_NUM_TELP ; NUM_TELEPHONE
NUM_VOIE ; DSC_VOIE ; CMPL_VOIE ; CD_POSTAL ; VILLE ; PAYS
TS_CREATION_PATIENT ; TS_MAJ_PATIENT
```

**PERSONNEL** — medical and administrative staff
```
ID_PERSONNEL ; NOM_PERSONNEL ; PRENOM_PERSONNEL ; FONCTION_PERSONNEL
TS_DEBUT_ACTIVITE ; TS_FIN_ACTIVITE ; RAISON_FIN_ACTIVITE
TS_CREATION_PERSONNEL ; TS_MAJ_PERSONNEL ; CD_STATUT_PERSONNEL
```

**CHAMBRE** — hospital rooms
```
NO_CHAMBRE ; NOM_CHAMBRE ; NO_ETAGE ; NOM_BATIMENT ; TYPE_CHAMBRE ; PRIX_JOUR ; DT_CREATION
```

**MEDICAMENT** — medication catalogue (reference / slowly changing)
```
CD_MEDICAMENT ; NOM_MEDICAMENT ; CONDIT_MEDICAMENT ; CATG_MEDICAMENT ; MARQUE_FABRI
```

**CONSULTATION** — central transactional table (one row = one patient visit)
```
ID_CONSULT ; ID_PERSONNEL ; ID_PATIENT
TS_DEBUT_CONSULT ; TS_FIN_CONSULT
POIDS_PATIENT ; TEMP_PATIENT ; UNIT_TEMP ; TENSION_PATIENT
DSC_PATHO ; INDIC_DIABETE ; ID_TRAITEMENT ; INDIC_HOSPI
```

**TRAITEMENT** — treatment prescribed during a consultation
```
ID_TRAITEMENT ; CD_MEDICAMENT ; CATG_MEDICAMENT ; MARQUE_FABRI
QTE_MEDICAMENT ; DSC_POSOLOGIE ; ID_CONSULT ; TS_CREATION_TRAITEMENT
```

**HOSPITALISATION** — inpatient stay linked to a consultation
```
ID_HOSPI ; ID_CONSULT_hospi ; NO_CHAMBRE_hospi
TS_DEBUT_HOSPI ; TS_FIN_HOSPI ; COUT_HOSPI ; ID_PERSONNEL_RESP
```

### Key relationships

```
PATIENT ──< CONSULTATION >── PERSONNEL
                │
                ├──< TRAITEMENT >── MEDICAMENT
                │
                └──< HOSPITALISATION >── CHAMBRE
                                    └── PERSONNEL (responsable)
```

- `CONSULTATION.INDIC_HOSPI = True` → a matching `HOSPITALISATION` row exists
- `CONSULTATION.ID_TRAITEMENT` → FK to `TRAITEMENT.ID_TRAITEMENT`
- `TRAITEMENT.ID_CONSULT` → FK back to `CONSULTATION.ID_CONSULT` (bidirectional link)
- Approximate volumes per batch: PATIENT ~643, CONSULTATION ~643, TRAITEMENT ~1312, HOSPITALISATION ~499, CHAMBRE ~787, MEDICAMENT ~2000, PERSONNEL ~200

---

## Project phases

| Sprint | Dates | Étape | Deliverables |
|---|---|---|---|
| Kick-off / Sprint 1 | 21/05 | Étape 1 | Environment setup, tool onboarding |
| Sprint 2 | 28/05 | Étape 1→2 | MPD design, source data ingestion into Staging |
| Sprint 3 | 03/06 | Étape 2→3 | KPI calculation, fact/dimension table population |
| Sprint 4 | 09/06 | Étape 3→4 | Power BI setup, reports and dashboards |
| End of project | 16/06 | Étape 4 | Final deliverables |
| Presentations | 18/06 | — | Project defence |

**Final deliverables**: dbt project, Airflow DAGs, Power BI dashboards.

---

## Repository structure (target)

```
bi-platform/
├── dbt/                        # dbt project root
│   ├── dbt_project.yml
│   ├── profiles.yml            # Snowflake connection (gitignored — use env vars)
│   ├── models/
│   │   ├── staging/            # 1:1 with source tables, minimal typing
│   │   ├── intermediate/       # Travail layer: joins, dedup, business rules
│   │   └── marts/              # Socle/Vue: fact + dimension tables for Power BI
│   ├── seeds/                  # Reference/lookup data (e.g. MEDICAMENT if stable)
│   ├── tests/                  # dbt data tests
│   └── macros/
├── airflow/
│   ├── dags/                   # One DAG per pipeline layer
│   └── plugins/
├── snowflake/
│   └── setup/                  # Database, schema, warehouse DDL scripts
├── inputs/                     # Source flat files (read-only — never modify)
│   ├── Data Hospital/          # Daily batches BDD_HOSPITAL_YYYYMMDD/
│   ├── Hopital CI VF.xlsx      # Data quality / integrity control rules
│   └── Hopital Mapping VF.xlsx # Source → target column mapping
├── instructions/               # Project brief PDFs (read-only reference)
└── CLAUDE.md
```

---

## dbt conventions

- **Staging models**: prefix `stg_`, one model per source table, cast types, rename columns to snake_case
- **Intermediate models**: prefix `int_`, business logic and joins
- **Mart models**: no prefix, named after the business concept (`fait_consultation`, `dim_patient`, `dim_personnel`, `dim_chambre`, `dim_medicament`, etc.)
- All models must have a `.yml` schema file with column descriptions and at least `not_null` + `unique` tests on PKs
- Snowflake credentials go in environment variables — never in `profiles.yml` committed to git

### Key dbt commands

```bash
dbt debug                             # test Snowflake connection
dbt run                               # run all models
dbt run --select staging              # run one layer
dbt run --select +fait_consultation   # run model + its upstream
dbt test                              # run all data tests
dbt test --select staging             # test one layer
dbt docs generate && dbt docs serve   # browse lineage locally
```

---

## Methodology

- **AGILE / SCRUM**: sprint kick-off (scope + tasks), daily sync, sprint retrospective + demo
- **GitLab**: source of truth for all code; one MR per feature / sprint deliverable
- **Teams + SharePoint**: project communication and documentation
- Branch naming: `feat/<topic>`, `fix/<topic>`, `sprint<N>/<topic>`
- Commit style (Conventional Commits): `feat: add stg_consultation model`, `fix: handle null ID_TRAITEMENT`

---

## Language policy

- **All code** (identifiers, comments, docstrings): **English**
- **Source column names**: keep original French names in staging (e.g. `ID_PATIENT`, `TS_DEBUT_CONSULT`), rename to English snake_case in intermediate/mart layers
- **dbt descriptions, Power BI labels, reports**: French (project audience is French-speaking)

---

## Coding standards

These rules apply to all Python written in this repo (Airflow DAGs, utilities, tests).
See also `.github/copilot-instructions.md` for the full reference (used by Copilot in IDE).

### Python environment

```bash
uv sync                              # create/update venv from pyproject.toml
uv run ruff check airflow/ tests/    # lint (replaces flake8 + isort)
uv run ruff format airflow/ tests/   # format (replaces black)
uv run mypy airflow/                 # strict type checking
uv run pytest                        # run tests
```

- Python **3.12** (pinned in `.python-version`)
- All dependencies declared in `pyproject.toml`; managed with **uv** — never `pip install` directly
- `profiles.yml` (dbt Snowflake creds) is gitignored — use environment variables loaded from `.env`

### Type annotations

Every function must have full parameter and return type annotations. `mypy --strict` must pass with zero errors.

```python
# ✅
def load_batch(batch_date: date, table: str) -> int: ...

# ❌
def load_batch(batch_date, table): ...
```

### Logging — never print()

One module-level logger per file. Use `%s` positional args — never f-strings in log calls (ruff rule `G`).

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Parsing row %d of %s", row_num, table)
logger.info("Loaded %d rows into %s.%s", n, schema, table)
logger.warning("Null value in column %s at row %d", col, i)
logger.error("Failed to load %s: %s", table, exc)
```

Each DAG / pipeline run must log: start time, batch date, rows loaded per table, total duration, rejected rows.
Logging is configured once at the entry point — never in library modules.

### Design rules

- **Single responsibility**: one function does one thing. If you need "and" to describe it, split it.
- **DRY**: extract any logic that appears more than once into a shared helper.
- **Google-style docstrings** on every public function, class, and module.
- **No bare `except`** — always catch specific exceptions.

### SQL / dbt

- Keywords `UPPERCASE`, one column per line, trailing comma style
- CTEs over subqueries — name each CTE after what it represents
- Always use `{{ ref() }}` / `{{ source() }}` — never hardcode schema names
- No `SELECT *` in intermediate or mart models
- No business logic in staging models (raw ingestion only)
