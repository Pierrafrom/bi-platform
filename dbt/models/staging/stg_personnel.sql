{{ config(materialized="view", schema="stg") }}

WITH source AS (

    SELECT * FROM {{ source("hospital", "personnel") }}

)

SELECT
    id_personnel                            AS staff_id,
    nom_personnel                           AS last_name,
    prenom_personnel                        AS first_name,
    fonction_personnel                      AS job_title,
    CAST(ts_debut_activite AS TIMESTAMP_NTZ) AS work_start_at,
    CAST(ts_fin_activite AS TIMESTAMP_NTZ)   AS work_end_at,
    raison_fin_activite                     AS work_end_reason,
    CAST(ts_creation_personnel AS TIMESTAMP_NTZ) AS created_at,
    CAST(ts_maj_personnel AS TIMESTAMP_NTZ)      AS updated_at,
    cd_statut_personnel                     AS status_code
FROM source
