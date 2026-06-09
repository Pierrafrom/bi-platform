{{ config(
    materialized="table",
    schema="soc",
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

-- SOC reference table for staff (personnel) identity.
-- Loaded from wrk_personnel OK rows only.
-- FK to r_part via staff_id / src_id where src_typ = job_title.

WITH source AS (

    SELECT
        staff_id,
        last_name,
        first_name,
        job_title,
        work_start_at,
        work_end_at,
        work_end_reason,
        status_code,
        created_at,
        updated_at,
        exec_id
    FROM {{ ref('wrk_personnel') }}
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    staff_id,
    last_name,
    first_name,
    job_title,
    work_start_at,
    work_end_at,
    work_end_reason,
    status_code,
    created_at,
    updated_at,
    exec_id
FROM source
