-- WRK model for HOSPITALISATION: quality control + deduplication.
-- Etape 1: mandatory field checks, date coherence (ended_at >= started_at).
-- Etape 2: dedup on hospi_id — keep most recent by started_at.

{{ config(
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

WITH source AS (

    SELECT
        hospi_id,
        consultation_id,
        room_number,
        responsible_staff_id,
        started_at,
        ended_at,
        cost
    FROM {{ ref('stg_hospitalisation') }}

),

quality_check AS (

    SELECT
        hospi_id,
        consultation_id,
        room_number,
        responsible_staff_id,
        started_at,
        ended_at,
        cost,
        CASE
            WHEN hospi_id IS NULL THEN 'REJ'
            WHEN hospi_id <= 0 THEN 'REJ'
            WHEN consultation_id IS NULL THEN 'REJ'
            WHEN room_number IS NULL THEN 'REJ'
            WHEN started_at IS NULL THEN 'REJ'
            WHEN ended_at IS NOT NULL AND ended_at < started_at THEN 'REJ'
            WHEN cost IS NOT NULL AND cost < 0 THEN 'REJ'
            ELSE 'OK'
        END AS wrk_stts_cd,
        CASE
            WHEN hospi_id IS NULL THEN 'NULL_MANDATORY'
            WHEN hospi_id <= 0 THEN 'WRONG_FORMAT'
            WHEN consultation_id IS NULL THEN 'NULL_MANDATORY'
            WHEN room_number IS NULL THEN 'NULL_MANDATORY'
            WHEN started_at IS NULL THEN 'NULL_MANDATORY'
            WHEN
                ended_at IS NOT NULL AND ended_at < started_at
                THEN 'WRONG_FORMAT'
            WHEN cost IS NOT NULL AND cost < 0 THEN 'WRONG_FORMAT'
        END AS rej_cod,
        NULL::VARCHAR(500) AS rej_dsc,
        '{{ var("batch_date", "1970-01-01") }}'::DATE AS batch_dt,
        {{ var("exec_id", -1) }} AS exec_id

    FROM source

),

ok_deduped AS (

    SELECT
        hospi_id,
        consultation_id,
        room_number,
        responsible_staff_id,
        started_at,
        ended_at,
        cost,
        wrk_stts_cd,
        rej_cod,
        rej_dsc,
        batch_dt,
        exec_id,
        ROW_NUMBER() OVER (
            PARTITION BY hospi_id
            ORDER BY started_at DESC
        ) AS rn
    FROM quality_check
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    hospi_id,
    consultation_id,
    room_number,
    responsible_staff_id,
    started_at,
    ended_at,
    cost,
    wrk_stts_cd,
    rej_cod,
    rej_dsc,
    batch_dt,
    exec_id
FROM ok_deduped
WHERE rn = 1

UNION ALL

SELECT
    hospi_id,
    consultation_id,
    room_number,
    responsible_staff_id,
    started_at,
    ended_at,
    cost,
    wrk_stts_cd,
    rej_cod,
    rej_dsc,
    batch_dt,
    exec_id
FROM quality_check
WHERE wrk_stts_cd = 'REJ'
