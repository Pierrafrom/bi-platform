{{ config(materialized="table", schema="soc") }}

WITH patients AS (

    SELECT
        patient_id AS src_id,
        'Patient' AS src_typ,
        exec_id
    FROM {{ ref("wrk_patient") }}
    WHERE wrk_stts_cd = 'OK'

),

personnel AS (

    SELECT
        staff_id AS src_id,
        job_title AS src_typ,
        exec_id
    FROM {{ ref("wrk_personnel") }}
    WHERE wrk_stts_cd = 'OK'

),

all_parties AS (

    SELECT
        src_id,
        src_typ,
        exec_id
    FROM patients
    UNION ALL
    SELECT
        src_id,
        src_typ,
        exec_id
    FROM personnel

)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY src_typ, src_id
    ) AS part_id,
    src_id,
    src_typ,
    exec_id
FROM all_parties
