{{ config(materialized="view", schema="vw") }}

-- KPI 6 : Occupation des chambres par période (jour / mois / année).
-- Grain : une ligne par (date, chambre) — les 786 chambres chaque jour.
-- is_occupied = 1 si une hospi couvre la chambre ce jour-là, sinon 0.
--
-- IMPORTANT — pourquoi un flag numérique et pas un statut texte agrégé :
-- une chambre peut être occupée certains jours et libre d'autres jours de la
-- même période. Compter un statut texte par DISTINCTCOUNT la classe alors dans
-- DEUX buckets → total > 786 (ex : avril donnait 631 occupées + 412 libres).
-- La classification doit se faire APRÈS le filtre de période, via une mesure :
--   Chambres occupées = CALCULATE(DISTINCTCOUNT([room_num]), [is_occupied] = 1)
--   Total chambres    = DISTINCTCOUNT([room_num])            -- = 786 constant
--   Chambres libres   = [Total chambres] - [Chambres occupées]
-- Définition retenue : une chambre est "libre" sur une période si aucun patient
-- n'y est passé pendant TOUTE la période (occupée 0 jour). Vrai pour jour, mois
-- et année car la mesure s'évalue sur le périmètre filtré.
--
-- Note : room 0 (chambre invalide rejetée par wrk_chambre) n'apparaît pas — le
-- CROSS JOIN sur r_room ne contient que les 786 chambres réelles.

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
    CASE WHEN occ.room_number IS NOT NULL THEN 1 ELSE 0 END AS is_occupied,
    CASE
        WHEN occ.room_number IS NOT NULL THEN 'Occupée'
        ELSE 'Libre'
    END AS occupancy_status
FROM all_rooms_per_period AS arp
LEFT JOIN occupied_on_date AS occ
    ON
        arp.room_num = occ.room_number
        AND arp.report_date = occ.report_date
