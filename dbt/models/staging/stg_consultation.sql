{{ config(materialized="view", schema="stg") }}

-- Staging model for the CONSULTATION source table.
-- Contract: 1:1 with the source file — type casting and renaming only.
-- No business logic, no joins, no filtering.

WITH source AS (

    SELECT * FROM {{ source('hospital', 'consultation') }}

),

renamed AS (

    SELECT
        -- Keys
        id_consult AS consultation_id,
        id_patient AS patient_id,
        id_personnel AS staff_id,
        id_traitement AS treatment_id,

        -- Vitals
        unit_temp AS temperature_unit,
        tension_patient AS blood_pressure,

        -- Diagnosis
        dsc_patho AS pathology_description,
        indic_diabete AS diabetes_indicator,
        indic_hospi AS hospitalisation_indicator,

        -- Timestamps
        TRY_TO_TIMESTAMP_NTZ(ts_debut_consult) AS started_at,
        TRY_TO_TIMESTAMP_NTZ(ts_fin_consult) AS ended_at,

        -- Vitals (measures)
        TRY_TO_DECIMAL(poids_patient, 6, 2) AS patient_weight_kg,
        TRY_TO_DECIMAL(temp_patient, 5, 2) AS patient_temperature

    FROM source

)

SELECT * FROM renamed
