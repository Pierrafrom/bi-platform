{{ config(materialized="view", schema="vw") }}

-- KPI 3 : Nombre de chambres distinctes ayant accueilli des patients
--         diagnostiqués d'une certaine pathologie, par période.
-- Power BI : filtres sur pathology_description, consultation_date
-- (année/mois/jour extraits nativement par Power BI depuis la DATE).

WITH hospi_pathology AS (

    SELECT
        fc.pathology_description,
        rh.room_number,
        DATE(fc.started_at) AS consultation_date
    FROM {{ ref('fait_consult') }} AS fc
    INNER JOIN {{ ref('r_hospi') }} AS rh
        ON fc.consultation_id = rh.consultation_id
    WHERE fc.pathology_description IS NOT NULL

)

SELECT
    pathology_description,
    consultation_date,
    COUNT(DISTINCT room_number) AS room_count
FROM hospi_pathology
GROUP BY
    pathology_description,
    consultation_date
