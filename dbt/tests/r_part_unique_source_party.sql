SELECT
    src_id,
    src_typ,
    COUNT(*) AS row_count
FROM {{ ref("r_part") }}
GROUP BY src_id, src_typ
HAVING COUNT(*) > 1
