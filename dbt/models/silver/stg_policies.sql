-- Latest known version of each policy. The full history lives in snap_policies.
with ranked as(
    SELECT
        *,
        row_number() OVER(
            PARTITION BY policy_id
            order by updated_at DESC, _loaded_at DESC
        )as rn
    from {{ source('bronze', 'raw_policies') }}
)

SELECT
    policy_id,
    customer_id,
    vehicle_id,
    upper(product_code) as product_code,
    try_to_date(start_date) as start_date,
    try_to_date(end_date) as end_date,
    status,
    try_to_decimal(annual_premium_eur, 10, 2) as annual_premium_eur,
    try_to_number(deductible_eur) as deductible_eur,
    try_to_number(no_claim_years) as no_claim_years,
    try_to_date(updated_at)::timestamp_ntz as updated_at
FROM ranked
WHERE rn = 1 