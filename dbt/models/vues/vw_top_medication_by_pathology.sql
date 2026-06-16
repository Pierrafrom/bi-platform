{{ config(materialized="view", schema="vw") }}

-- KPI 2 : Médicament le plus prescrit (en quantité) par pathologie et période.
-- rank_by_quantity = 1 : médicament n°1 par (pathologie, consultation_date).
-- Power BI : filtres sur pathology_description, consultation_date
-- (année/mois/jour extraits nativement par Power BI depuis la DATE).

WITH prescriptions AS (

    SELECT
        fc.pathology_description,
        rt.medicine_code,
        rt.medicine_category,
        rt.manufacturer_brand,
        rm.medc_name AS medicine_name,
        DATE(fc.started_at) AS consultation_date,
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

),

aggregated AS (

    SELECT
        pathology_description,
        consultation_date,
        medicine_code,
        medicine_name,
        medicine_category,
        manufacturer_brand,
        SUM(quantity) AS total_quantity
    FROM prescriptions
    GROUP BY
        pathology_description,
        consultation_date,
        medicine_code,
        medicine_name,
        medicine_category,
        manufacturer_brand

)

SELECT
    pathology_description,
    consultation_date,
    medicine_code,
    medicine_name,
    medicine_category,
    manufacturer_brand,
    total_quantity,
    ROW_NUMBER() OVER (
        PARTITION BY
            pathology_description, consultation_date
        ORDER BY total_quantity DESC, medicine_code ASC
    ) AS rank_by_quantity
FROM aggregated
