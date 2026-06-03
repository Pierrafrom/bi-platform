{{ config(materialized="view", schema="stg") }}

-- Staging model for the PATIENT source table.
-- Contract: 1:1 with the source file — type casting and renaming only.
-- No business logic, no joins, no filtering.

WITH source AS (

    SELECT * FROM {{ source('hospital', 'patient') }}

),

renamed AS (

    SELECT
        -- Keys
        id_patient                                          AS patient_id,

        -- Identity
        nom_patient                                         AS last_name,
        prenom_patient                                      AS first_name,
        num_secu                                            AS social_security_number,

        -- Birth
        CAST(dt_naiss AS DATE)                             AS birth_date,
        ville_naiss                                         AS birth_city,
        pays_naiss                                          AS birth_country,

        -- Contact
        num_telephone                                       AS phone_number,
        ind_pays_num_telp                                   AS phone_country_code,

        -- Address
        num_voie                                            AS street_number,
        dsc_voie                                            AS street_name,
        cmpl_voie                                           AS address_complement,
        cd_postal                                           AS postal_code,
        ville                                               AS city,
        pays                                                AS country,

        -- Audit
        CAST(ts_creation_patient AS TIMESTAMP_NTZ)          AS created_at,
        CAST(ts_maj_patient AS TIMESTAMP_NTZ)               AS updated_at

    FROM source

)

SELECT * FROM renamed
