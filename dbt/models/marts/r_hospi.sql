{{ config(
    materialized="table",
    schema="soc",
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

-- SOC table for hospitalisations.
-- Loaded from wrk_hospitalisation OK rows only.
-- Duration in days is derived from started_at / ended_at.

WITH source AS (

    SELECT
        hospi_id,
        consultation_id,
        room_number,
        responsible_staff_id,
        started_at,
        ended_at,
        cost,
        exec_id
    FROM {{ ref('wrk_hospitalisation') }}
    WHERE wrk_stts_cd = 'OK'

)

SELECT
    hospi_id,
    consultation_id,
    room_number,
    responsible_staff_id,
    started_at,
    ended_at,
    cost,
    exec_id,
    DATEDIFF('day', started_at, ended_at) AS duration_days
FROM source
