{{ config(materialized="view", schema="vw") }}

-- KPI 5 : Proportion de patients hospitalisés ayant séjourné au moins une nuit,
--         par période de début d'hospitalisation.
-- Au moins une nuit = a franchi au moins un minuit ET séjour >= 8h réelles.
-- DATE(ended_at) > DATE(started_at) garantit la présence nocturne effective
-- (un séjour 09h-18h fait 9h mais ne passe pas minuit → exclu).
-- DATEDIFF('hour') >= 8 écarte les courts passages de minuit (ex: 23h45-00h30).
-- La data source n'ayant aucune hospi débutant et finissant le même jour
-- calendaire, le faux 100% venait du DATEDIFF('day') précédent qui comptait
-- tout franchissement de minuit comme "une nuit".
-- Seuil 8h = définition standard d'une nuitée hospitalière (PMSI).
-- Power BI : filtres sur report_date (année/mois/jour extraits nativement).

WITH stays AS (

    SELECT
        hospi_id,
        DATE(started_at) AS report_date,
        CASE
            WHEN
                DATE(ended_at) > DATE(started_at)
                AND DATEDIFF('hour', started_at, ended_at) >= 8
                THEN 1
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
