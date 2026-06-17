{{ config(materialized="view", schema="vw") }}

-- KPI 6 : Chambres non occupées par période.
-- Grain : une ligne par (date, chambre).
-- Une chambre est "Occupée" le jour J si une hospi vérifie
-- DATE(started_at) <= J AND DATE(ended_at) >= J.
-- Le JOIN mois-niveau précédent marquait toute chambre ayant eu UNE hospi
-- dans le mois comme "Occupée" chaque jour du mois — d'où le faux 100%.
-- Power BI filtre sur occupancy_status = 'Libre'.

WITH periods AS (

    SELECT DISTINCT DATE(started_at) AS report_date
    FROM {{ ref('fait_consult') }}

),

occupied_on_date AS (

    SELECT DISTINCT
        rh.room_number,
        p.report_date
    FROM {{ ref('r_hospi') }} AS rh
    INNER JOIN periods AS p
        ON
            DATE(rh.started_at) <= p.report_date
            AND (
                rh.ended_at IS NULL
                OR DATE(rh.ended_at) >= p.report_date
            )

),

all_rooms_per_period AS (

    SELECT
        p.report_date,
        r.room_num,
        r.room_name,
        r.room_typ,
        r.buld_name
    FROM periods AS p
    CROSS JOIN {{ ref('r_room') }} AS r

)

SELECT
    arp.report_date,
    arp.room_num,
    arp.room_name,
    arp.room_typ,
    arp.buld_name,
    CASE
        WHEN occ.room_number IS NOT NULL THEN 'Occupée'
        ELSE 'Libre'
    END AS occupancy_status
FROM all_rooms_per_period AS arp
LEFT JOIN occupied_on_date AS occ
    ON
        arp.room_num = occ.room_number
        AND arp.report_date = occ.report_date
