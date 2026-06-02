# AGENTS.md

This file provides guidance to AI coding assistants (Codex, GitHub Copilot, ChatGPT, Claude Code, etc.) when working in this repository.

## Project Context

NF26 university project at UTC, supervised by SMART TEEM (data consulting firm).

Goal: build a complete Business Intelligence decision-support platform based on:
- Snowflake Data Warehouse
- dbt transformations
- Apache Airflow orchestration
- Power BI reporting

Important rule:

> Work only with requirements defined for the current sprint. Do not implement features, models, reports, or assumptions from future sprints.

---

## Technology Stack

| Tool | Purpose |
|--------|----------|
| Snowflake | Cloud Data Warehouse |
| dbt | Data transformation layer |
| Apache Airflow | Pipeline orchestration |
| Power BI | Reporting and dashboards |
| GitLab | Version control and CI/CD |

---

## Data Architecture

Flat Files
→ Snowflake
→ Staging / ODS
→ Travail
→ Socle / Vue
→ Power BI

### Layer Responsibilities

#### Staging / ODS
- Raw ingestion
- Data quality controls
- Rejected row management
- No business logic

#### Travail
- Data cleansing
- Deduplication
- Standardization
- Business rules

#### Socle / Vue
- Fact tables
- Dimension tables
- Historical tracking
- Star or Snowflake schema
- Consumption layer for Power BI

---

## dbt Conventions

### Staging Models
- Prefix: stg_
- One model per source table
- Type casting only
- No business logic

### Intermediate Models
- Prefix: int_
- Business rules
- Joins
- Deduplication

### Mart Models
Examples:
- fait_consultation
- dim_patient
- dim_personnel
- dim_chambre
- dim_medicament

Requirements:
- Business-oriented naming
- Fact and dimension modeling

### Testing
Every model must include:
- Schema YAML
- Column descriptions
- Primary key uniqueness tests
- Primary key not-null tests

---

## SQL Rules

Always use:
- {{ ref() }}
- {{ source() }}

Never use SELECT * in intermediate or mart layers.

Prefer:
- CTEs
- Explicit column lists
- Uppercase SQL keywords
- One column per line

---

## Language Policy

### Code
Everything must be written in English:
- Variables
- Functions
- Classes
- Comments
- Docstrings

### Business Documentation
Keep French for:
- dbt descriptions
- Power BI labels
- User-facing reports

---

## Python Standards

### Environment

Python 3.12

Dependency management:
- uv sync
- uv run pytest
- uv run ruff check
- uv run ruff format
- uv run mypy

Never use pip install directly.

### Type Annotations

All functions must include complete type annotations.

Example:

def load_batch(batch_date: date, table: str) -> int:
    ...

### Logging

Never use print().

Always use:

import logging
logger = logging.getLogger(__name__)

Use positional formatting:
logger.info("Loaded %d rows into %s", rows, table)

Never use f-strings in log calls.

---

## Design Principles

### Single Responsibility Principle
One function = one responsibility.

### DRY
Extract duplicated logic into reusable helpers.

### Exceptions
Never use bare except clauses.

Always catch specific exceptions.

### Documentation
Every public:
- module
- class
- function

must contain Google-style docstrings.

---

## Git Workflow

Branch naming:
- feat/<topic>
- fix/<topic>
- sprint<N>/<topic>

Commit naming:
- feat: add staging model
- fix: handle null values

---

## Expectations for AI Coding Assistants

1. Respect the current sprint scope.
2. Follow repository architecture.
3. Follow dbt conventions.
4. Follow Python standards.
5. Preserve naming conventions.
6. Do not introduce speculative future features.
7. Prefer readability over cleverness.
8. Generate tests whenever relevant.
9. Explain significant architectural decisions.
10. Never modify source input files.
