{{ config(
    materialized="table",
    schema="soc",
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

-- SOC fact table for consultations — central grain of the star schema.
-- One row per consultation. Loaded from wrk_consultation OK rows only.
-- Duration in minutes is derived from started_at / ended_at.

WITH source AS (

    SELECT
        consultation_id,
        patient_id,
        staff_id,
        treatment_id,
        started_at,
        ended_at,
        patient_weight_kg,
        patient_temperature,
        temperature_unit,
        blood_pressure,
        pathology_description,
        diabetes_indicator,
        hospitalisation_indicator,
        exec_id
    FROM {{ ref('wrk_consultation') }}
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    consultation_id,
    patient_id,
    staff_id,
    treatment_id,
    started_at,
    ended_at,
    patient_weight_kg,
    patient_temperature,
    temperature_unit,
    blood_pressure,
    pathology_description,
    diabetes_indicator,
    hospitalisation_indicator,
    exec_id,
    DATEDIFF('minute', started_at, ended_at) AS duration_minutes
FROM source
