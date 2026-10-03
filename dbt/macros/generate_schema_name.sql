{#
    By default dbt prefixes custom schemas with the target schema (SILVER_GOLD).
    We want the layer names exactly as they are: SILVER and GOLD.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim | upper }}
    {%- endif -%}
{%- endmacro %}
