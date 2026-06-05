SELECT
    patient_id,
    COUNT(*) AS ok_row_count
FROM {{ ref("wrk_patient") }}
WHERE wrk_stts_cd = 'OK'
GROUP BY patient_id
HAVING COUNT(*) > 1