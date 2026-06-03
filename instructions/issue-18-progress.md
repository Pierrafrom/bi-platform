# Issue 18 - Party Model R_PART

## Objectif

Construire la chaine dbt du Party Model pour la couche SOC :

- `stg_personnel`
- `wrk_patient`
- `wrk_personnel`
- `r_part`
- schemas YAML et tests dbt associes

## Avancement

- [x] Issue analysee depuis le contenu fourni par l'utilisateur.
- [x] Etat initial du projet verifie.
- [x] Incoherence dbt/Snowflake identifiee : schemas dbt custom a stabiliser.
- [x] Modeles dbt crees.
- [x] Schemas YAML ajoutes ou completes.
- [x] Validation whitespace `git diff --check` effectuee.
- [ ] Validation dbt a lancer apres installation de `dbt`/`uv`.

## Notes

- Le depot GitHub est prive, l'issue n'est pas accessible via API sans authentification.
- L'environnement local actuel ne dispose pas de `uv`, `pytest`, `ruff` ni `mypy`.
- L'environnement local actuel ne dispose pas de `dbt`.
- Le Python local detecte est `3.10.7`, alors que le projet demande Python `>=3.12`.
