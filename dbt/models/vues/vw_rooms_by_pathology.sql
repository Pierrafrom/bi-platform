{{ config(materialized="view", schema="vw") }}

-- KPI 3 : Chambres ayant accueilli des patients diagnostiqués d'une certaine
-- pathologie. Grain détaillé : une ligne par hospitalisation. Power BI compte
-- les chambres distinctes via DISTINCTCOUNT(room_number) — correct sur toute
-- période (pré-agréger un room_count par jour le rendrait faux sur plusieurs
-- jours).

SELECT
    fc.pathology_description,
    rh.room_number,
    DATE(fc.started_at) AS report_date
FROM {{ ref('fait_consult') }} AS fc
INNER JOIN {{ ref('r_hospi') }} AS rh
    ON fc.consultation_id = rh.consultation_id
INNER JOIN {{ ref('r_room') }} AS rr
    ON rh.room_number = rr.room_num
WHERE fc.pathology_description IS NOT NULL
