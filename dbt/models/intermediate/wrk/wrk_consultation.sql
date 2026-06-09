-- WRK model for CONSULTATION: quality control + deduplication.
-- Etape 1: mandatory field checks, date coherence (ended_at >= started_at).
-- Etape 2: dedup on consultation_id — keep most recent by started_at.

{{ config(
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

WITH source AS (

    SELECT
        consultation_id,
        patient_id,
        staff_id,
        treatment_id,
        temperature_unit,
        blood_pressure,
        pathology_description,
        diabetes_indicator,
        hospitalisation_indicator,
        started_at,
        ended_at,
        patient_weight_kg,
        patient_temperature
    FROM {{ ref('stg_consultation') }}

),

quality_check AS (

    SELECT
        consultation_id,
        patient_id,
        staff_id,
        treatment_id,
        temperature_unit,
        blood_pressure,
        pathology_description,
        diabetes_indicator,
        hospitalisation_indicator,
        started_at,
        ended_at,
        patient_weight_kg,
        patient_temperature,
        CASE
            WHEN consultation_id IS NULL THEN 'REJ'
            WHEN consultation_id <= 0 THEN 'REJ'
            WHEN patient_id IS NULL THEN 'REJ'
            WHEN staff_id IS NULL THEN 'REJ'
            WHEN started_at IS NULL THEN 'REJ'
            WHEN ended_at IS NULL THEN 'REJ'
            WHEN ended_at < started_at THEN 'REJ'
            ELSE 'OK'
        END AS wrk_stts_cd,
        CASE
            WHEN consultation_id IS NULL THEN 'NULL_MANDATORY'
            WHEN consultation_id <= 0 THEN 'WRONG_FORMAT'
            WHEN patient_id IS NULL THEN 'NULL_MANDATORY'
            WHEN staff_id IS NULL THEN 'NULL_MANDATORY'
            WHEN started_at IS NULL THEN 'NULL_MANDATORY'
            WHEN ended_at IS NULL THEN 'NULL_MANDATORY'
            WHEN ended_at < started_at THEN 'WRONG_FORMAT'
        END AS rej_cod,
        NULL::VARCHAR(500) AS rej_dsc,
        '{{ var("batch_date", "1970-01-01") }}'::DATE AS batch_dt,
        {{ var("exec_id", -1) }} AS exec_id

    FROM source

),

ok_deduped AS (

    SELECT
        consultation_id,
        patient_id,
        staff_id,
        treatment_id,
        temperature_unit,
        blood_pressure,
        pathology_description,
        diabetes_indicator,
        hospitalisation_indicator,
        started_at,
        ended_at,
        patient_weight_kg,
        patient_temperature,
        wrk_stts_cd,
        rej_cod,
        rej_dsc,
        batch_dt,
        exec_id,
        ROW_NUMBER() OVER (
            PARTITION BY consultation_id
            ORDER BY started_at DESC
        ) AS rn
    FROM quality_check
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    consultation_id,
    patient_id,
    staff_id,
    treatment_id,
    temperature_unit,
    blood_pressure,
    pathology_description,
    diabetes_indicator,
    hospitalisation_indicator,
    started_at,
    ended_at,
    patient_weight_kg,
    patient_temperature,
    wrk_stts_cd,
    rej_cod,
    rej_dsc,
    batch_dt,
    exec_id
FROM ok_deduped
WHERE rn = 1

UNION ALL

SELECT
    consultation_id,
    patient_id,
    staff_id,
    treatment_id,
    temperature_unit,
    blood_pressure,
    pathology_description,
    diabetes_indicator,
    hospitalisation_indicator,
    started_at,
    ended_at,
    patient_weight_kg,
    patient_temperature,
    wrk_stts_cd,
    rej_cod,
    rej_dsc,
    batch_dt,
    exec_id
FROM quality_check
WHERE wrk_stts_cd = 'REJ'
