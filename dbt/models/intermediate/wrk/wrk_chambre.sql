-- WRK model for CHAMBRE: quality control + deduplication.
-- Etape 1: mandatory field checks, positive values.
-- Etape 2: dedup on room_number — keep most recent by created_date.
-- No normalisation step (no unit conversions for CHAMBRE).
-- No surrogate key resolution (ROOM_NUM is the natural PK in SOC).

{{ config(
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

WITH source AS (

    SELECT * FROM {{ ref('stg_chambre') }}

),

quality_check AS (

    SELECT
        *,
        CASE
            WHEN room_number IS NULL THEN 'REJ'
            WHEN room_number <= 0 THEN 'REJ'
            WHEN room_name IS NULL THEN 'REJ'
            WHEN day_rate IS NULL THEN 'REJ'
            WHEN day_rate <= 0 THEN 'REJ'
            WHEN created_date IS NULL THEN 'REJ'
            ELSE 'OK'
        END AS wrk_stts_cd,
        CASE
            WHEN room_number IS NULL THEN 'NULL_MANDATORY'
            WHEN room_number <= 0 THEN 'WRONG_FORMAT'
            WHEN room_name IS NULL THEN 'NULL_MANDATORY'
            WHEN day_rate IS NULL THEN 'NULL_MANDATORY'
            WHEN day_rate <= 0 THEN 'WRONG_FORMAT'
            WHEN created_date IS NULL THEN 'NULL_MANDATORY'
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
            PARTITION BY room_number
            ORDER BY created_date DESC
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
