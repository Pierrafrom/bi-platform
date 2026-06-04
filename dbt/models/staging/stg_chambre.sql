-- Staging model for the CHAMBRE source table.
-- Contract: 1:1 with the source file — type casting and renaming only.
-- No business logic, no joins, no filtering.

WITH source AS (

    SELECT * FROM {{ source('hospital', 'chambre') }}

),

renamed AS (

    SELECT
        -- Key
        no_chambre AS room_number,

        -- Attributes
        nom_chambre AS room_name,
        no_etage AS floor_number,
        nom_batiment AS building_name,
        type_chambre AS room_type,
        prix_jour AS day_rate,

        -- Dates
        TRY_TO_DATE(dt_creation, 'YYYY-MM-DD') AS created_date

    FROM source

)

SELECT * FROM renamed
