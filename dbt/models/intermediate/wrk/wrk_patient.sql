{{ config(materialized="table", schema="wrk") }}

WITH source AS (

    SELECT
        patient_id,
        last_name,
        first_name,
        social_security_number,
        birth_date,
        birth_city,
        birth_country,
        phone_number,
        phone_country_code,
        street_number,
        street_name,
        address_complement,
        postal_code,
        city,
        country,
        created_at,
        updated_at
    FROM {{ ref("stg_patient") }}

),

quality_check AS (

    SELECT
        patient_id,
        last_name,
        first_name,
        social_security_number,
        birth_date,
        birth_city,
        birth_country,
        phone_number,
        phone_country_code,
        street_number,
        street_name,
        address_complement,
        postal_code,
        city,
        country,
        created_at,
        updated_at,
        CASE
            WHEN patient_id IS NULL THEN 'REJ'
            WHEN patient_id <= 0 THEN 'REJ'
            WHEN last_name IS NULL THEN 'REJ'
            WHEN first_name IS NULL THEN 'REJ'
            WHEN created_at IS NULL THEN 'REJ'
            WHEN updated_at IS NULL THEN 'REJ'
            ELSE 'OK'
        END AS wrk_stts_cd,
        CASE
            WHEN patient_id IS NULL THEN 'NULL_MANDATORY'
            WHEN patient_id <= 0 THEN 'WRONG_FORMAT'
            WHEN last_name IS NULL THEN 'NULL_MANDATORY'
            WHEN first_name IS NULL THEN 'NULL_MANDATORY'
            WHEN created_at IS NULL THEN 'NULL_MANDATORY'
            WHEN updated_at IS NULL THEN 'NULL_MANDATORY'
            ELSE NULL
        END AS rej_cod,
        CAST(NULL AS VARCHAR(500)) AS rej_dsc,
        '{{ var("batch_date") }}'::DATE AS batch_dt,
        {{ var("exec_id") }} AS exec_id
    FROM source

),

ok_deduped AS (

    SELECT
        patient_id,
        last_name,
        first_name,
        social_security_number,
        birth_date,
        birth_city,
        birth_country,
        phone_number,
        phone_country_code,
        street_number,
        street_name,
        address_complement,
        postal_code,
        city,
        country,
        created_at,
        updated_at,
        wrk_stts_cd,
        rej_cod,
        rej_dsc,
        batch_dt,
        exec_id,
        ROW_NUMBER() OVER (
            PARTITION BY patient_id
            ORDER BY updated_at DESC, created_at DESC
        ) AS rn
    FROM quality_check
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    patient_id,
    last_name,
    first_name,
    social_security_number,
    birth_date,
    birth_city,
    birth_country,
    phone_number,
    phone_country_code,
    street_number,
    street_name,
    address_complement,
    postal_code,
    city,
    country,
    created_at,
    updated_at,
    wrk_stts_cd,
    rej_cod,
    rej_dsc,
    batch_dt,
    exec_id
FROM ok_deduped
WHERE rn = 1

UNION ALL

SELECT
    patient_id,
    last_name,
    first_name,
    social_security_number,
    birth_date,
    birth_city,
    birth_country,
    phone_number,
    phone_country_code,
    street_number,
    street_name,
    address_complement,
    postal_code,
    city,
    country,
    created_at,
    updated_at,
    wrk_stts_cd,
    rej_cod,
    rej_dsc,
    batch_dt,
    exec_id
FROM quality_check
WHERE wrk_stts_cd = 'REJ'
