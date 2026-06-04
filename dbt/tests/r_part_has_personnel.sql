SELECT 'missing personnel population' AS failure_reason
WHERE NOT EXISTS (
    SELECT 1
    FROM {{ ref("r_part") }}
    WHERE src_typ <> 'Patient'
)
