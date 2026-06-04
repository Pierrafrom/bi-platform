-- Staging model for the MEDICAMENT source table.
-- Contract: 1:1 with the source file — type casting and renaming only.
-- No business logic, no joins, no filtering.

WITH source AS (

    SELECT * FROM {{ source('hospital', 'medicament') }}

),

renamed AS (

    SELECT
        -- Composite PK
        cd_medicament AS medicine_code,
        catg_medicament AS medicine_category,
        marque_fabri AS manufacturer_brand,

        -- Attributes
        nom_medicament AS medicine_name,
        condit_medicament AS medicine_packaging

    FROM source

)

SELECT * FROM renamed
