{{ config(materialized="view", schema="stg") }}

-- Staging model for the HOSPITALISATION source table.
-- Contract: 1:1 with the source file — type casting and renaming only.
-- No business logic, no joins, no filtering.

WITH source AS (

    SELECT * FROM {{ source('hospital', 'hospitalisation') }}

),

renamed AS (

    SELECT
        -- Keys
        id_hospi AS hospi_id,
        id_consult_hospi AS consultation_id,
        no_chambre_hospi AS room_number,
        id_personnel_resp AS responsible_staff_id,

        -- Stay
        TRY_TO_TIMESTAMP_NTZ(ts_debut_hospi) AS started_at,
        TRY_TO_TIMESTAMP_NTZ(ts_fin_hospi) AS ended_at,
        TRY_TO_DECIMAL(cout_hospi, 10, 2) AS cost

    FROM source

)

SELECT * FROM renamed
