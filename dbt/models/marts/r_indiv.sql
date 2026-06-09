{{ config(
    materialized="table",
    schema="soc",
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

-- SOC reference table for individual (patient) identity.
-- Loaded from wrk_patient OK rows only.
-- FK to r_part via patient_id / src_id where src_typ = 'Patient'.

WITH source AS (

    SELECT
        patient_id,
        last_name,
        first_name,
        social_security_number,
        birth_date,
        birth_city,
        birth_country,
        created_at,
        updated_at,
        exec_id
    FROM {{ ref('wrk_patient') }}
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    patient_id AS indiv_id,
    last_name,
    first_name,
    social_security_number,
    birth_date,
    birth_city,
    birth_country,
    created_at,
    updated_at,
    exec_id
FROM source
