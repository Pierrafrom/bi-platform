-- Fails if any room_number appears more than once among OK rows.
-- The dedup step in wrk_chambre must guarantee exactly one OK row per room.
SELECT
    room_number,
    COUNT(*) AS cnt
FROM {{ ref('wrk_chambre') }}
WHERE WRK_STTS_CD = 'OK'
GROUP BY room_number
HAVING COUNT(*) > 1
