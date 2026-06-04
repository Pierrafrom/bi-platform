-- Post-hook macro: mark a model execution as finished in TCH.T_SUIV_TRMT.
-- No-op when exec_id is -1 (local dev run without Airflow vars).
{% macro end_exec(exec_id, status) %}
    {%- if exec_id != -1 -%}
        UPDATE TCH.T_SUIV_TRMT
        SET
            EXEC_END_DTTM = CURRENT_TIMESTAMP(),
            EXEC_STTS_CD  = '{{ status }}'
        WHERE EXEC_ID = {{ exec_id }}
    {%- else -%}
        SELECT 1
    {%- endif -%}
{% endmacro %}
