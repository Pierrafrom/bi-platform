# bi-platform

NF26 — Mise en place d'une solution décisionnelle
**Datawarehouse Snowflake + Reporting Power BI**

Projet universitaire UTC, encadré par [SMART TEEM](https://www.smartteem.fr/).

## Stack technique

| Outil | Rôle |
|---|---|
| Snowflake | Cloud DWH (Staging → Travail → Socle/Vue) |
| dbt | Transformations SQL |
| Apache Airflow | Orchestration des DAGs |
| Power BI | Reporting et tableaux de bord |
| GitLab / GitHub | Versioning |

## Architecture

```text
inputs/Data Hospital/BDD_HOSPITAL_YYYYMMDD/
        │  (7 fichiers .txt, séparateur ;, 1 batch/jour)
        ▼
   Snowflake
   ├── Staging / ODS   (contrôle / rejet)
   ├── Travail         (qualité, unification)
   └── Socle / Vue     (historisation, KPIs)  ──► Power BI
        dbt  ──  Airflow
```

## Domaine métier

Source : plateforme hospitalière
Tables : `PATIENT`, `PERSONNEL`, `CHAMBRE`, `MEDICAMENT`, `CONSULTATION`, `TRAITEMENT`, `HOSPITALISATION`

## Lancer dbt

```bash
cp .env.example .env   # renseigner les credentials Snowflake
dbt debug              # tester la connexion
dbt run                # exécuter tous les modèles
dbt test               # lancer les tests de données
dbt docs generate && dbt docs serve  # explorer la lignée
```

## Structure du repo

```text
bi-platform/
├── dbt/            # modèles, tests, macros, seeds
├── airflow/        # DAGs d'orchestration
├── snowflake/      # DDL setup (databases, schemas, warehouses)
├── inputs/         # fichiers sources (lecture seule)
└── instructions/   # briefs projet (PDF, read-only)
```
