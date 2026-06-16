{{ config(materialized="view", schema="vw") }}

-- KPI 2 : Quantités de médicaments prescrits par pathologie et période.
-- Grain : une ligne par (pathologie, date, médicament). Pas de rang
-- pré-calculé : un rang par jour empêcherait de déterminer le médicament le
-- plus prescrit sur une période de plusieurs jours. Power BI resomme
-- total_quantity par médicament puis classe via une mesure DAX (TOPN).
-- medicine_name retombe sur medicine_code si non référencé dans r_medc,
-- pour éviter une cellule vide dans le visuel Top 1 côté Power BI.

WITH prescriptions AS (

    SELECT
        fc.pathology_description,
        rt.medicine_code,
        rt.medicine_category,
        rt.manufacturer_brand,
        COALESCE(rm.medc_name, rt.medicine_code) AS medicine_name,
        DATE(fc.started_at) AS report_date,
        COALESCE(rt.medicine_quantity, 0) AS quantity
    FROM {{ ref('fait_consult') }} AS fc
    INNER JOIN {{ ref('r_trmt') }} AS rt
        ON fc.treatment_id = rt.treatment_id
    LEFT JOIN {{ ref('r_medc') }} AS rm
        ON
            rt.medicine_code = rm.medc_cd
            AND rt.medicine_category = rm.medc_catg
            AND rt.manufacturer_brand = rm.manf_brnd
    WHERE fc.pathology_description IS NOT NULL

)

SELECT
    pathology_description,
    report_date,
    medicine_code,
    medicine_name,
    medicine_category,
    manufacturer_brand,
    SUM(quantity) AS total_quantity
FROM prescriptions
GROUP BY
    pathology_description,
    report_date,
    medicine_code,
    medicine_name,
    medicine_category,
    manufacturer_brand
