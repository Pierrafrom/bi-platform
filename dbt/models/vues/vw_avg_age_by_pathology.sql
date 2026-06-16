{{ config(materialized="view", schema="vw") }}

-- KPI 1 : Âge moyen des patients par pathologie et période.
-- Power BI : filtres sur pathology_description, report_date
-- (année/mois/jour extraits nativement par Power BI depuis la DATE).
-- report_date est nommé de façon générique (et identique dans les 6 vues)
-- pour pouvoir le relier à une seule table de dates côté Power BI.

WITH consultations AS (

    SELECT
        fc.patient_id,
        fc.pathology_description,
        ri.birth_date,
        fc.started_at,
        DATE(fc.started_at) AS report_date
    FROM {{ ref('fait_consult') }} AS fc
    INNER JOIN {{ ref('r_indiv') }} AS ri
        ON fc.patient_id = ri.indiv_id
    WHERE
        fc.pathology_description IS NOT NULL
        AND ri.birth_date IS NOT NULL

)

SELECT
    pathology_description,
    report_date,
    ROUND(AVG(FLOOR(DATEDIFF('day', birth_date, started_at) / 365.25)), 1)
        AS avg_age_at_consultation,
    COUNT(DISTINCT patient_id) AS patient_count
FROM consultations
GROUP BY
    pathology_description,
    report_date
