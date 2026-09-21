# bi-platform

[![Checks](https://img.shields.io/badge/ruff%20%7C%20mypy%20--strict%20%7C%20pytest-passing-brightgreen)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue)](.python-version)
[![dbt](https://img.shields.io/badge/dbt-Snowflake-blue?logo=dbt)](dbt/dbt_project.yml)

End-to-end BI decision-support platform: a Snowflake data warehouse fed
daily from flat files, transformed with dbt through three governed layers,
orchestrated by Airflow, and served to Power BI dashboards.

## Context

Built for **NF26** (decision-support systems course, UTC), a 4-sprint group
project for [SMART TEEM](https://www.smartteem.fr/), a data-consulting firm
that supervised the deliverables and grading. Team of 6; I drove most of
the dbt modeling and pipeline work (majority of commits) alongside the
Airflow orchestration.

The brief: take daily flat-file exports from a fictional hospital's
information system and turn them into governed, historized, query-ready
tables a hospital's management could actually build dashboards on — room
occupancy, consultations by pathology, prescribing patterns by department.

## Architecture

```text
inputs/Data Hospital/BDD_HOSPITAL_YYYYMMDD/
        │  (7 files, ; separated, 1 batch/day)
        ▼
   Snowflake
   ├── Staging / ODS   (ingestion, quality control, rejection)
   ├── Travail         (deduplication, business-rule unification)
   └── Socle / Vue     (historized facts/dimensions, KPIs)  ──► Power BI
        dbt (transformations) ── Airflow (orchestration)
```

Source tables: `PATIENT`, `PERSONNEL`, `CHAMBRE`, `MEDICAMENT`,
`CONSULTATION`, `TRAITEMENT`, `HOSPITALISATION` — a small OLTP-shaped
hospital schema (patients, staff, rooms, consultations, prescriptions,
stays) reshaped into a Kimball-style star schema in the Socle/Vue layer.

## Stack

| Layer | Tool |
|---|---|
| Data warehouse | Snowflake |
| Transformations | dbt (staging → intermediate → marts) |
| Orchestration | Apache Airflow |
| Reporting | Power BI |
| Pipeline utilities | Python 3.12, `uv`, `ruff`, `mypy --strict` |
| CI | GitHub Actions (lint, type-check, dbt build) |

## Running the dbt project

```bash
cp .env.example .env   # fill in Snowflake credentials
dbt debug              # test the connection
dbt run                # build all models
dbt test                # run data quality tests
dbt docs generate && dbt docs serve  # browse the lineage graph
```

## Repository structure

```text
bi-platform/
├── dbt/            # models (staging/intermediate/marts), tests, macros
├── airflow/        # orchestration DAGs
├── snowflake/      # database/schema/warehouse setup DDL
├── inputs/         # source flat files (read-only)
└── instructions/   # original project brief (read-only reference)
```

## Contributors

Pierre Fromont Boissel, Lucas, Mathéo Gros, Rania Alami, Robin Lanfranchi, EMeyzenq.
