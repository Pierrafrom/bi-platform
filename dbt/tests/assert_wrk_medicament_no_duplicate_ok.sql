-- Fails if any composite business key appears more than once among OK rows.
-- The dedup step in wrk_medicament must guarantee at most one OK row
-- per (medicine_code, medicine_category, manufacturer_brand).
SELECT
    medicine_code,
    medicine_category,
    manufacturer_brand,
    COUNT(*) AS cnt
FROM {{ ref('wrk_medicament') }}
WHERE WRK_STTS_CD = 'OK'
GROUP BY medicine_code, medicine_category, manufacturer_brand
HAVING COUNT(*) > 1
