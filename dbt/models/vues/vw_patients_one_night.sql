{{ config(materialized="view", schema="vw") }}

-- KPI 5 : Proportion de patients hospitalisés ayant séjourné au moins une nuit,
--         par période de début d'hospitalisation.
-- Au moins une nuit = duration_days >= 1 (ended_at - started_at ≥ 1 jour).
-- Power BI : filtres sur hospi_year, hospi_month.

WITH stays AS (

    SELECT
        hospi_id,
        YEAR(started_at) AS hospi_year,
        MONTH(started_at) AS hospi_month,
        CASE
            WHEN duration_days IS NOT NULL AND duration_days >= 1 THEN 1
            ELSE 0
        END AS is_one_night_plus
    FROM {{ ref('r_hospi') }}

)

SELECT
    hospi_year,
    hospi_month,
    COUNT(*) AS total_hospitalisations,
    SUM(is_one_night_plus) AS one_night_plus_count,
    ROUND(100.0 * SUM(is_one_night_plus) / COUNT(*), 2) AS one_night_plus_pct
FROM stays
GROUP BY
    hospi_year,
    hospi_month
