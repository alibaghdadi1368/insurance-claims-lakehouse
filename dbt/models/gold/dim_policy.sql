-- Every version of every policy (premium changes, cancellations).
SELECT
    dbt_scd_id as policy_key,
    policy_id,
    customer_id,
    vehicle_id,
    product_code,
    start_date,
    end_date,
    status,
    annual_premium_eur,
    deductible_eur,
    no_claim_years,
    dbt_valid_from                   as valid_from,
    dbt_valid_to                     as valid_to,
    dbt_valid_to is null             as is_current
FROM {{ ref('snap_policies') }}