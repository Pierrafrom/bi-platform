{{ config(materialized="view", schema="vw") }}

-- KPI 4 : Proportion de médecins par spécialité (job_title) ayant diagnostiqué
--         une pathologie donnée, par période.
-- doctor_proportion_pct = médecins de cette spécialité /
--                         total médecins pour la pathologie.
-- Power BI : filtres sur pathology_description, consultation_date
-- (année/mois/jour extraits nativement par Power BI depuis la DATE).

WITH consultations AS (

    SELECT
        fc.pathology_description,
        rs.staff_id,
        rs.job_title,
        DATE(fc.started_at) AS consultation_date
    FROM {{ ref('fait_consult') }} AS fc
    INNER JOIN {{ ref('r_stf') }} AS rs
        ON fc.staff_id = rs.staff_id
    WHERE fc.pathology_description IS NOT NULL

),

by_specialty AS (

    SELECT
        pathology_description,
        consultation_date,
        job_title,
        COUNT(DISTINCT staff_id) AS doctor_count
    FROM consultations
    GROUP BY
        pathology_description,
        consultation_date,
        job_title

),

totals AS (

    SELECT
        pathology_description,
        consultation_date,
        SUM(doctor_count) AS total_doctors
    FROM by_specialty
    GROUP BY
        pathology_description,
        consultation_date

)

SELECT
    bs.pathology_description,
    bs.consultation_date,
    bs.job_title AS specialty,
    bs.doctor_count,
    t.total_doctors,
    ROUND(100.0 * bs.doctor_count / t.total_doctors, 2) AS doctor_proportion_pct
FROM by_specialty AS bs
INNER JOIN totals AS t
    ON
        bs.pathology_description = t.pathology_description
        AND bs.consultation_date = t.consultation_date
