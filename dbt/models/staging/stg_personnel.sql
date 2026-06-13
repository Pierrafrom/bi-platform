{{ config(materialized="view", schema="stg") }}

WITH source AS (

    SELECT * FROM {{ source("hospital", "personnel") }}

),

renamed AS (

    SELECT
        id_personnel AS staff_id,
        nom_personnel AS last_name,
        prenom_personnel AS first_name,
        fonction_personnel AS job_title,
        ts_debut_activite::TIMESTAMP_NTZ AS work_start_at,
        ts_fin_activite::TIMESTAMP_NTZ AS work_end_at,
        raison_fin_activite AS work_end_reason,
        ts_creation_personnel::TIMESTAMP_NTZ AS created_at,
        ts_maj_personnel::TIMESTAMP_NTZ AS updated_at,
        cd_statut_personnel AS status_code
    FROM source

)

SELECT * FROM renamed
