{{ config(materialized="view", schema="vw") }}

-- KPI 4 : Médecins (par spécialité) ayant diagnostiqué une pathologie donnée.
-- Grain détaillé : une ligne par consultation. Power BI calcule les médecins
-- distincts via DISTINCTCOUNT(staff_id) et la proportion par spécialité via
-- DAX — corrects sur toute période (pré-agréger un doctor_count par jour le
-- rendrait faux sur plusieurs jours).

SELECT
    fc.pathology_description,
    rs.staff_id,
    rs.job_title AS specialty,
    DATE(fc.started_at) AS report_date
FROM {{ ref('fait_consult') }} AS fc
INNER JOIN {{ ref('r_stf') }} AS rs
    ON fc.staff_id = rs.staff_id
WHERE fc.pathology_description IS NOT NULL
