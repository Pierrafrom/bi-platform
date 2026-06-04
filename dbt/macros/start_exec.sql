-- Pre-hook macro: mark a model execution as started in TCH.T_SUIV_TRMT.
-- No-op when run_id is not provided (local dev run without Airflow vars).
{% macro start_exec(script_name) %}
    {%- if var("run_id", none) is not none -%}
        INSERT INTO TCH.T_SUIV_TRMT (RUN_ID, SCRPT_NAME, EXEC_STRT_DTTM, EXEC_STTS_CD)
        VALUES (
            {{ var('run_id') }},
            '{{ script_name }}',
            CURRENT_TIMESTAMP(),
            'ENC'
        )
    {%- else -%}
        SELECT 1
    {%- endif -%}
{% endmacro %}
