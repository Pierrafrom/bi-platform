-- Override dbt's default schema generation.
-- Default behavior: <target_schema>_<custom_schema> — creates e.g. PUBLIC_WRK.
-- This override uses the custom schema name directly (uppercased),
-- matching the Snowflake schemas created by the DDL (STG, WRK, OBS, REJ, SOC, TCH).
-- If no custom schema is set, falls back to the target schema.
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim | upper }}
    {%- endif -%}
{%- endmacro %}
