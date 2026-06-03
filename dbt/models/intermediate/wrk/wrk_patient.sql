{{ config(materialized="table", schema="wrk") }}

WITH source AS (

    SELECT * FROM {{ ref("stg_patient") }}

),

quality_check AS (

    SELECT
        *,
        CASE
            WHEN patient_id IS NULL THEN 'REJ'
            WHEN patient_id <= 0 THEN 'REJ'
            WHEN last_name IS NULL THEN 'REJ'
            WHEN first_name IS NULL THEN 'REJ'
            WHEN created_at IS NULL THEN 'REJ'
            WHEN updated_at IS NULL THEN 'REJ'
            ELSE 'OK'
        END AS wrk_stts_cd,
        CASE
            WHEN patient_id IS NULL THEN 'NULL_MANDATORY'
            WHEN patient_id <= 0 THEN 'WRONG_FORMAT'
            WHEN last_name IS NULL THEN 'NULL_MANDATORY'
            WHEN first_name IS NULL THEN 'NULL_MANDATORY'
            WHEN created_at IS NULL THEN 'NULL_MANDATORY'
            WHEN updated_at IS NULL THEN 'NULL_MANDATORY'
            ELSE NULL
        END AS rej_cod,
        CAST(NULL AS VARCHAR(500)) AS rej_dsc,
        '{{ var("batch_date") }}'::DATE AS batch_dt,
        {{ var("exec_id") }} AS exec_id
    FROM source

),

ok_deduped AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY patient_id
            ORDER BY updated_at DESC, created_at DESC
        ) AS rn
    FROM quality_check
    WHERE wrk_stts_cd = 'OK'

)

SELECT * EXCLUDE (rn)
FROM ok_deduped
WHERE rn = 1

UNION ALL

SELECT *
FROM quality_check
WHERE wrk_stts_cd = 'REJ'
