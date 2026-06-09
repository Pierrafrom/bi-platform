{{ config(
    materialized="table",
    schema="soc",
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

-- SOC reference table for postal addresses.
-- One row per patient — extracted from wrk_patient OK rows.
-- Rows with no address data (all address fields NULL) are excluded.

WITH source AS (

    SELECT
        patient_id,
        street_number,
        street_name,
        address_complement,
        postal_code,
        city,
        country,
        exec_id
    FROM {{ ref('wrk_patient') }}
    WHERE wrk_stts_cd = 'OK'

),

with_address AS (

    SELECT *
    FROM source
    WHERE
        street_name IS NOT NULL
        OR postal_code IS NOT NULL
        OR city IS NOT NULL

)

SELECT
    patient_id AS indiv_id,
    street_number,
    street_name,
    address_complement,
    postal_code,
    city,
    country,
    exec_id
FROM with_address
