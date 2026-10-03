-- Every version of every customer. is_current marks the latest one.
SELECT
    dbt_scd_id as customer_key,
    customer_id,
    first_name,
    last_name,
    date_of_birth,
    email,
    postcode,
    pc4,
    city,
    customer_since,
    dbt_valid_from as valid_from,
    dbt_valid_to as valid_to,
    dbt_valid_to is null as is_current
FROM {{ ref('snap_customers') }}