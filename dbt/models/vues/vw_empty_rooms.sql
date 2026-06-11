{{ config(materialized="view", schema="vw") }}

-- KPI 6 : Chambres non occupées par période.
-- Génère une ligne par (période, chambre).
-- Power BI filtre sur occupancy_status = 'Libre'.
-- Les périodes sont dérivées des hospitalisations existantes.

WITH periods AS (

    SELECT DISTINCT
        YEAR(started_at) AS hospi_year,
        MONTH(started_at) AS hospi_month
    FROM {{ ref('r_hospi') }}

),

occupied_rooms AS (

    SELECT DISTINCT
        room_number,
        YEAR(started_at) AS hospi_year,
        MONTH(started_at) AS hospi_month
    FROM {{ ref('r_hospi') }}

),

all_rooms_per_period AS (

    SELECT
        p.hospi_year,
        p.hospi_month,
        r.room_num,
        r.room_name,
        r.room_typ,
        r.buld_name
    FROM periods AS p
    CROSS JOIN {{ ref('r_room') }} AS r

)

SELECT
    arp.hospi_year,
    arp.hospi_month,
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
