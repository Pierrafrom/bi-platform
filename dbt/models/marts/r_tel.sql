{{ config(
    materialized="table",
    schema="soc",
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

-- SOC reference table for phone numbers.
-- One row per patient — extracted from wrk_patient OK rows.
-- Rows with no phone data are excluded.

WITH source AS (

    SELECT
        patient_id,
        phone_country_code,
        phone_number,
        exec_id
    FROM {{ ref('wrk_patient') }}
    WHERE wrk_stts_cd = 'OK'

),

with_phone AS (

    SELECT *
    FROM source
    WHERE phone_number IS NOT NULL

)

SELECT
    patient_id AS indiv_id,
    phone_country_code,
    phone_number,
    exec_id
FROM with_phone
