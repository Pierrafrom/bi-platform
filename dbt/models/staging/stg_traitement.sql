{{ config(materialized="view", schema="stg") }}

-- Staging model for the TRAITEMENT source table.
-- Contract: 1:1 with the source file — type casting and renaming only.
-- No business logic, no joins, no filtering.

WITH source AS (

    SELECT * FROM {{ source('hospital', 'traitement') }}

),

renamed AS (

    SELECT
        -- Keys
        id_traitement AS treatment_id,
        id_consult AS consultation_id,
        cd_medicament AS medicine_code,

        -- Medication details (denormalised in source)
        catg_medicament AS medicine_category,
        marque_fabri AS manufacturer_brand,

        -- Prescription
        dsc_posologie AS dosage_description,
        TRY_TO_DECIMAL(qte_medicament, 8, 3) AS medicine_quantity,

        -- Audit
        TRY_TO_TIMESTAMP_NTZ(ts_creation_traitement) AS created_at

    FROM source

)

SELECT * FROM renamed
