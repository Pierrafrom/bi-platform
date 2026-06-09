{{ config(
    materialized="table",
    schema="soc",
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

-- SOC reference table for treatments.
-- Loaded from wrk_traitement OK rows only.

WITH source AS (

    SELECT
        treatment_id,
        consultation_id,
        medicine_code,
        medicine_category,
        manufacturer_brand,
        medicine_quantity,
        dosage_description,
        created_at,
        exec_id
    FROM {{ ref('wrk_traitement') }}
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    treatment_id,
    consultation_id,
    medicine_code,
    medicine_category,
    manufacturer_brand,
    medicine_quantity,
    dosage_description,
    created_at,
    exec_id
FROM source
