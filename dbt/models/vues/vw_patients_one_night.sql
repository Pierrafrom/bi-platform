{{ config(materialized="view", schema="vw") }}

-- KPI 5 : Proportion de patients hospitalisés ayant séjourné au moins une nuit,
--         par période de début d'hospitalisation.
-- Au moins une nuit = duration_days >= 1 (ended_at - started_at ≥ 1 jour).
-- Power BI : filtres sur report_date (année/mois/jour extraits nativement).
-- report_date = date de début d'hospitalisation, nommé de façon générique
-- (identique dans les 6 vues) pour le relier à une seule table de dates.

WITH stays AS (

    SELECT
        hospi_id,
        DATE(started_at) AS report_date,
        CASE
            WHEN duration_days IS NOT NULL AND duration_days >= 1 THEN 1
            ELSE 0
        END AS is_one_night_plus
    FROM {{ ref('r_hospi') }}

)

SELECT
    report_date,
    COUNT(*) AS total_hospitalisations,
    SUM(is_one_night_plus) AS one_night_plus_count,
    ROUND(100.0 * SUM(is_one_night_plus) / COUNT(*), 2) AS one_night_plus_pct
FROM stays
GROUP BY
    report_date
