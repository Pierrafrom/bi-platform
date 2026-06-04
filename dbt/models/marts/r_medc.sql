-- SOC reference table for medications.
-- MEDC_ID: surrogate key via ROW_NUMBER on composite business key
-- (medicine_code, medicine_category, manufacturer_brand). No IDENTITY.
-- Source: wrk_medicament, OK rows only.

{{ config(
    pre_hook="{{ start_exec(this.name) }}",
    post_hook="{{ end_exec(var('exec_id', -1), 'OK') }}"
) }}

SELECT
    medicine_code AS medc_cd,
    medicine_name AS medc_name,
    medicine_packaging AS medc_cond,
    medicine_category AS medc_catg,
    manufacturer_brand AS manf_brnd,
    exec_id,
    ROW_NUMBER() OVER (
        ORDER BY medicine_code, medicine_category, manufacturer_brand
    ) AS medc_id

FROM {{ ref('wrk_medicament') }}
WHERE wrk_stts_cd = 'OK'
