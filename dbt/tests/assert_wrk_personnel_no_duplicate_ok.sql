SELECT
    staff_id,
    COUNT(*) AS ok_row_count
FROM {{ ref("wrk_personnel") }}
WHERE wrk_stts_cd = 'OK'
GROUP BY staff_id
HAVING COUNT(*) > 1