-- WRK model for MEDICAMENT: quality control + deduplication.
-- Etape 1: mandatory field checks on composite PK (code + category + brand).
-- Etape 2: dedup on (medicine_code, medicine_category, manufacturer_brand).
-- No normalisation or surrogate key step for MEDICAMENT at WRK layer.

{{ config(
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

WITH source AS (

    SELECT * FROM {{ ref('stg_medicament') }}

),

quality_check AS (

    SELECT
        *,
        CASE
            WHEN medicine_code IS NULL THEN 'REJ'
            WHEN medicine_category IS NULL THEN 'REJ'
            WHEN manufacturer_brand IS NULL THEN 'REJ'
            ELSE 'OK'
        END AS wrk_stts_cd,
        CASE
            WHEN medicine_code IS NULL THEN 'NULL_MANDATORY'
            WHEN medicine_category IS NULL THEN 'NULL_MANDATORY'
            WHEN manufacturer_brand IS NULL THEN 'NULL_MANDATORY'
        END AS rej_cod,
        NULL::VARCHAR(500) AS rej_dsc,
        '{{ var("batch_date", "1970-01-01") }}'::DATE AS batch_dt,
        {{ var("exec_id", -1) }} AS exec_id

    FROM source

),

deduped AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY medicine_code, medicine_category, manufacturer_brand
            ORDER BY medicine_name
        ) AS rn
    FROM quality_check
    WHERE wrk_stts_cd = 'OK'

)

SELECT * EXCLUDE (rn) FROM deduped
WHERE rn = 1

UNION ALL

SELECT * EXCLUDE (rn)
FROM (SELECT
    *,
    1 AS rn
FROM quality_check
WHERE wrk_stts_cd = 'REJ')
WHERE rn = 1
