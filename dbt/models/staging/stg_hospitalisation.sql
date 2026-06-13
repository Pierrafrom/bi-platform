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
        id_consult AS consultation_id,
        no_chambre AS room_number,
        id_personnel_resp AS responsible_staff_id,

        -- Stay
        ts_debut_hospi::TIMESTAMP_NTZ AS started_at,
        ts_fin_hospi::TIMESTAMP_NTZ AS ended_at,
        cout_hospi::DECIMAL(10, 2) AS cost

    FROM source

)

SELECT * FROM renamed
