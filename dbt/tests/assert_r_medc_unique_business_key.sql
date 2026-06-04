-- Fails if the composite business key (MEDC_CD, MEDC_CATG, MANF_BRND)
-- is not unique in r_medc. Since MEDC_ID is derived from ROW_NUMBER on
-- this key, duplicates here would produce non-deterministic surrogate keys.
SELECT
    MEDC_CD,
    MEDC_CATG,
    MANF_BRND,
    COUNT(*) AS cnt
FROM {{ ref('r_medc') }}
GROUP BY MEDC_CD, MEDC_CATG, MANF_BRND
HAVING COUNT(*) > 1
