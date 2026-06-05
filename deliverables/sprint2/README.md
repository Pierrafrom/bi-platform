# Sprint 2 — Étape 2 : Ingestion STG

**Projet** : NF26 BI Platform — SMART TEEM / UTC
**Période** : 28/05 → 03/06/2026
**Équipe** : Pierre Fromont Boissel

---

## Objectif

Mettre en place la chaîne complète d'ingestion des données hospitalières, depuis les fichiers plats jusqu'aux tables de référence Snowflake, via dbt.

---

## Ce qui a été livré

### 1. Pipeline d'ingestion (Python)

`pipeline/ingest/ingest_stg.py`

Script Python qui charge les 7 fichiers sources d'un batch quotidien (`BDD_HOSPITAL_YYYYMMDD/`) dans les tables STG de Snowflake. Pour chaque table : lecture du fichier, validation des colonnes attendues, chargement avec SQL typé. Chaque exécution trace : heure de début, lignes chargées par table, lignes rejetées, durée totale.

Usage :
```bash
python pipeline/ingest/ingest_stg.py --batch-date 2026-04-29
```

### 2. Modèles dbt — couche Staging (STG)

`dbt/models/staging/`

| Modèle | Source |
|---|---|
| `stg_patient` | PATIENT |
| `stg_personnel` | PERSONNEL |
| `stg_chambre` | CHAMBRE |
| `stg_medicament` | MEDICAMENT |

Chaque modèle effectue uniquement le renommage snake_case et le cast de types (`TRY_TO_DATE`, `TRY_TO_TIMESTAMP_NTZ`). Aucune logique métier.

### 3. Modèles dbt — couche Travail (WRK)

`dbt/models/intermediate/wrk/`

| Modèle | Contrôles |
|---|---|
| `wrk_patient` | Non-nullité des champs obligatoires, format date |
| `wrk_personnel` | Non-nullité, déduplication sur `staff_id` |
| `wrk_chambre` | Non-nullité, taux journalier > 0 |
| `wrk_medicament` | Non-nullité sur la clé composite |

Chaque modèle ajoute `wrk_stts_cd` (OK/REJ), `rej_cod`, `batch_dt`, `exec_id`.

### 4. Modèles dbt — couche Socle (SOC)

`dbt/models/marts/`

| Modèle | Description |
|---|---|
| `r_room` | Table de référence chambre (lignes OK uniquement) |
| `r_medc` | Table de référence médicament (clé de substitution par ROW_NUMBER) |
| `r_part` | Table unifiée patient/personnel (clé déterministe sur `src_typ` + `src_id`) |

### 5. DDL Snowflake

`snowflake/`

- `00_create_databases.sql` — création de `HOPITAL_DW` et des schémas (STG, WRK, REJ, SOC, TCH)
- `01_create_stg_tables.sql` — DDL des 7 tables STG
- `06_create_tch_tables.sql` — tables de tracking `T_SUIV_RUN` / `T_SUIV_TRMT`

### 6. Orchestration Airflow

`airflow/dags/dag_daily_pipeline.py`

DAG quotidien qui enchaîne :

```
start_run → ingest_stg → dbt_run → dbt_test → end_run
```

Le tracking TCH est intégré : chaque exécution crée une ligne `T_SUIV_RUN` (statut ENC → OK ou KO). Les credentials Snowflake sont lus depuis des variables d'environnement.

### 7. CI/CD

`.github/workflows/ci.yml`

À chaque push : lint SQL (sqlfluff), validation Python (ruff + mypy), `dbt parse` (validation du projet dbt sans connexion Snowflake), exécution des tests unitaires.

---

## Tests unitaires

`tests/pipeline/test_ingest_stg.py` — couverture de la lecture des fichiers sources, validation des colonnes, et logique d'ingestion (sans connexion Snowflake requise).

```bash
uv run pytest tests/pipeline/test_ingest_stg.py
```

---

## Prochaine étape — Sprint 3

Calcul des KPIs, alimentation des tables de faits et dimensions (`fait_consultation`, `dim_patient`, `dim_personnel`…).
