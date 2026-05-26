# Documentation technique — bi-platform

Source de vérité : `inputs/Hopital Mapping VF.xlsx` et `inputs/Hopital CI VF.xlsx`.

## Fichiers

| #   | Fichier                            | Couche  | Description                                     |
| --- | ---------------------------------- | ------- | ----------------------------------------------- |
| 1   | [01-staging.md](01-staging.md)     | **STG** | Ingestion des fichiers plats → Snowflake        |
| 2   | [02-obs.md](02-obs.md)             | **OBS** | Archive brute des données STG (historisation)   |
| 3   | [03-wrk.md](03-wrk.md)             | **WRK** | Travail : qualité, dédoublonnage, normalisation |
| 4   | [04-rej.md](04-rej.md)             | **REJ** | Rejets de qualité et recyclage                  |
| 5   | [05-socle.md](05-socle.md)         | **SOC** | Socle final (Party Model) après bascule         |
| 6   | [06-technique.md](06-technique.md) | **TCH** | Suivi pipeline run / script                     |

---

## Architecture globale

```mermaid
flowchart TD
    subgraph SRC["📁 Fichiers source (inputs/)"]
        F["TABLE_YYYYMMDD.txt\n7 tables · quotidien · UTF-8 · ;\nContrat d'interface : Hopital CI VF.xlsx"]
    end

    subgraph SNF["❄️ Snowflake"]
        subgraph STG["STG — Staging"]
            S["Ingestion brute\nCast types · Header check\nAucune logique métier"]
        end

        subgraph OBS["OBS — Observation"]
            O["Archive des données STG\nDurée d'historisation configurable\nBase de rejeu et d'audit"]
        end

        subgraph WRK["WRK — Work / Travail"]
            W1["1- Contrôle qualité\n(règles CI)"]
            W2["2- Dédoublonnage"]
            W3["3- Normalisation\n(temp C/F, booléens…)"]
            W4["4- Résolution\nsurrogate keys"]
            W1 --> W2 --> W3 --> W4
        end

        subgraph REJ["REJ — Rejet"]
            R["Lignes KO avec\ncode + motif de rejet\nRecyclage possible"]
        end

        subgraph SOC["SOC — Socle"]
            SC["Party Model validé\nR_PART · R_ROOM · R_MEDC\nO_CONS · O_TRET · O_HOSP\nO_INDV · O_STFF · O_TELP · O_ADDR"]
        end

        subgraph TCH["TCH — Technique"]
            T["T_SUIV_RUN\nT_SUIV_TRMT\nTraçabilité EXEC_ID"]
        end

        S -->|"archive\nbatch"| O
        S -->|"chargement"| W1
        W4 -->|"lignes KO"| R
        W4 -->|"BASCULE\n(lignes OK)"| SC
        R -.->|"recyclage\naprès correction"| W1
        SC -.->|"EXEC_ID"| T
        WRK -.->|"EXEC_ID"| T
    end

    F -->|"Airflow DAG\nIngestion quotidienne"| S

    PBI["📊 Power BI"]
    SC --> PBI
```

---

## Rôle de chaque couche

| Couche  | Question clé                                      | Ce qu'elle répond                                               |
| ------- | ------------------------------------------------- | --------------------------------------------------------------- |
| **STG** | _Qu'est-ce que le système source nous a envoyé ?_ | Copie exacte des fichiers plats, typée                          |
| **OBS** | _Peut-on rejouer un batch passé ?_                | Archive horodatée, durée de rétention configurable              |
| **WRK** | _Ces données sont-elles exploitables ?_           | Qualité, dédup, normalisation — seules les lignes OK continuent |
| **REJ** | _Que faire des données mauvaises ?_               | Stockage avec motif, possibilité de correction et recyclage     |
| **SOC** | _Quel est l'état de référence validé ?_           | Party Model propre, prêt pour Power BI                          |
| **TCH** | _Qui a chargé cette ligne et quand ?_             | Traçabilité complète de chaque exécution                        |

---

## Mapping couches ↔ dbt

| Couche Snowflake | Couche dbt                 | Matérialisation                     |
| ---------------- | -------------------------- | ----------------------------------- |
| STG              | `models/staging/`          | view                                |
| OBS              | `models/intermediate/obs/` | table (partitionnée par batch_date) |
| WRK              | `models/intermediate/wrk/` | table                               |
| REJ              | `models/intermediate/rej/` | table (append)                      |
| SOC              | `models/marts/`            | table                               |
