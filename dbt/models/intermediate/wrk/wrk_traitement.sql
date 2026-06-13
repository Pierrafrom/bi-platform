-- WRK model for TRAITEMENT: quality control + deduplication.
-- Etape 1: mandatory fields (treatment_id, consultation_id, medicine_code,
--          medicine_category, manufacturer_brand).
-- Etape 2: dedup on treatment_id — keep most recent by created_at.

{{ config(
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

WITH source AS (

    SELECT
        treatment_id,
        consultation_id,
        medicine_code,
        medicine_category,
        manufacturer_brand,
        dosage_description,
        medicine_quantity,
        created_at
    FROM {{ ref('stg_traitement') }}

),

quality_check AS (

    SELECT
        treatment_id,
        consultation_id,
        medicine_code,
        medicine_category,
        manufacturer_brand,
        dosage_description,
        medicine_quantity,
        created_at,
        CASE
            WHEN treatment_id IS NULL THEN 'REJ'
            WHEN treatment_id <= 0 THEN 'REJ'
            WHEN consultation_id IS NULL THEN 'REJ'
            WHEN medicine_code IS NULL THEN 'REJ'
            WHEN medicine_category IS NULL THEN 'REJ'
            WHEN manufacturer_brand IS NULL THEN 'REJ'
            WHEN dosage_description IS NULL THEN 'REJ'
            ELSE 'OK'
        END AS wrk_stts_cd,
        CASE
            WHEN treatment_id IS NULL THEN 'NULL_MANDATORY'
            WHEN treatment_id <= 0 THEN 'WRONG_FORMAT'
            WHEN consultation_id IS NULL THEN 'NULL_MANDATORY'
            WHEN medicine_code IS NULL THEN 'NULL_MANDATORY'
            WHEN medicine_category IS NULL THEN 'NULL_MANDATORY'
            WHEN manufacturer_brand IS NULL THEN 'NULL_MANDATORY'
            WHEN dosage_description IS NULL THEN 'NULL_MANDATORY'
        END AS rej_cod,
        NULL::VARCHAR(500) AS rej_dsc,
        '{{ var("batch_date", "1970-01-01") }}'::DATE AS batch_dt,
        {{ var("exec_id", -1) }} AS exec_id

    FROM source

),

ok_deduped AS (

    SELECT
        treatment_id,
        consultation_id,
        medicine_code,
        medicine_category,
        manufacturer_brand,
        dosage_description,
        medicine_quantity,
        created_at,
        wrk_stts_cd,
        rej_cod,
        rej_dsc,
        batch_dt,
        exec_id,
        ROW_NUMBER() OVER (
            PARTITION BY treatment_id
            ORDER BY created_at DESC NULLS LAST, treatment_id ASC
        ) AS rn
    FROM quality_check
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    treatment_id,
    consultation_id,
    medicine_code,
    medicine_category,
    manufacturer_brand,
    dosage_description,
    medicine_quantity,
    created_at,
    wrk_stts_cd,
    rej_cod,
    rej_dsc,
    batch_dt,
    exec_id
FROM ok_deduped
WHERE rn = 1

UNION ALL

SELECT
    treatment_id,
    consultation_id,
    medicine_code,
    medicine_category,
    manufacturer_brand,
    dosage_description,
    medicine_quantity,
    created_at,
    wrk_stts_cd,
    rej_cod,
    rej_dsc,
    batch_dt,
    exec_id
FROM quality_check
WHERE wrk_stts_cd = 'REJ'
