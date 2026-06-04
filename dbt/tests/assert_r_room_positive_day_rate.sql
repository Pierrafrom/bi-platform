-- Fails if any room in the SOC layer has a day rate that is null or not positive.
-- WRK already filters these out, so a failure here indicates a pipeline gap.
SELECT
    ROOM_NUM,
    ROOM_DAY_RATE
FROM {{ ref('r_room') }}
WHERE ROOM_DAY_RATE IS NULL OR ROOM_DAY_RATE <= 0
