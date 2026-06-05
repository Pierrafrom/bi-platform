{{ config(materialized="view", schema="stg") }}

WITH source AS (

    SELECT * FROM {{ source("hospital", "personnel") }}

),

renamed AS (

    SELECT
        id_personnel                            AS staff_id,
        nom_personnel                           AS last_name,
        prenom_personnel                        AS first_name,
        fonction_personnel                      AS job_title,
        TRY_TO_TIMESTAMP_NTZ(ts_debut_activite)  AS work_start_at,
        TRY_TO_TIMESTAMP_NTZ(ts_fin_activite)    AS work_end_at,
        raison_fin_activite                     AS work_end_reason,
        TRY_TO_TIMESTAMP_NTZ(ts_creation_personnel) AS created_at,
        TRY_TO_TIMESTAMP_NTZ(ts_maj_personnel)      AS updated_at,
        cd_statut_personnel                     AS status_code
    FROM source

)

SELECT * FROM renamed
