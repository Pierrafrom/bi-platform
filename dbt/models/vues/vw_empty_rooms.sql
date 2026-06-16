{{ config(materialized="view", schema="vw") }}

-- KPI 6 : Chambres non occupées par période.
-- Génère une ligne par (période, chambre).
-- Power BI filtre sur occupancy_status = 'Libre'.
-- periods dérivé de fait_consult pour inclure les mois sans hospi.
-- hospi_year/hospi_month restent dans les CTE internes (occupied_rooms,
-- periods, all_rooms_per_period) : l'occupation n'est connue qu'au mois
-- (pas de table jour par jour dans r_hospi), donc le JOIN doit rester sur
-- année+mois. Seul le SELECT final exposé à Power BI a été nettoyé
-- (hospi_year/hospi_month redondants avec hospi_date supprimés en sortie).

WITH occupied_rooms AS (

    SELECT DISTINCT
        room_number,
        YEAR(started_at) AS hospi_year,
        MONTH(started_at) AS hospi_month
    FROM {{ ref('r_hospi') }}

),

periods AS (

    SELECT DISTINCT
        DATE(started_at) AS hospi_date,
        YEAR(started_at) AS hospi_year,
        MONTH(started_at) AS hospi_month,
        DAY(started_at) AS hospi_day
    FROM {{ ref('fait_consult') }}

),

all_rooms_per_period AS (

    SELECT
        p.hospi_date,
        p.hospi_year,
        p.hospi_month,
        p.hospi_day,
        r.room_num,
        r.room_name,
        r.room_typ,
        r.buld_name
    FROM periods AS p
    CROSS JOIN {{ ref('r_room') }} AS r

)

SELECT
    arp.hospi_date,
    arp.hospi_day,
    arp.room_num,
    arp.room_name,
    arp.room_typ,
    arp.buld_name,
    CASE
        WHEN orr.room_number IS NOT NULL THEN 'Occupée'
        ELSE 'Libre'
    END AS occupancy_status
FROM all_rooms_per_period AS arp
LEFT JOIN occupied_rooms AS orr
    ON
        arp.room_num = orr.room_number
        AND arp.hospi_year = orr.hospi_year
        AND arp.hospi_month = orr.hospi_month
