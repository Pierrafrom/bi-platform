-- SOC reference table for hospital rooms.
-- Natural PK: ROOM_NUM — stable room number, no surrogate key needed.
-- Source: wrk_chambre, OK rows only.

{{ config(
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

SELECT
    room_number AS room_num,
    room_name,
    floor_number AS flor_num,
    building_name AS buld_name,
    room_type AS room_typ,
    day_rate AS room_day_rate,
    created_date AS crtn_dt,
    exec_id

FROM {{ ref('wrk_chambre') }}
WHERE wrk_stts_cd = 'OK'
