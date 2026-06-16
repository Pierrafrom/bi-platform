{{ config(materialized="view", schema="vw") }}

-- KPI 1 : Âge des patients au moment de la consultation, par pathologie.
-- Grain détaillé : une ligne par consultation (pas de pré-agrégation).
-- Power BI calcule l'âge moyen via AVERAGE(age_at_consultation) et le nombre
-- de patients via DISTINCTCOUNT(patient_id) — corrects sur toute période.

SELECT
    fc.pathology_description,
    fc.patient_id,
    DATE(fc.started_at) AS report_date,
    FLOOR(DATEDIFF('day', ri.birth_date, fc.started_at) / 365.25)
        AS age_at_consultation
FROM {{ ref('fait_consult') }} AS fc
INNER JOIN {{ ref('r_indiv') }} AS ri
    ON fc.patient_id = ri.indiv_id
WHERE
    fc.pathology_description IS NOT NULL
    AND ri.birth_date IS NOT NULL
