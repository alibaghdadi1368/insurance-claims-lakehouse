-- uses qualify, Snowflake's shortcut for filtering on a window function without a subquery.
SELECT
    payment_id,
    policy_id,
    try_to_date(due_date) as due_date,
    try_to_decimal(amount_eur, 10, 2) as amount_eur,
    try_to_date(paid_date) as paid_date,
    payment_method
FROM {{ source('bronze', 'raw_premiums') }}
qualify row_number() OVER(PARTITION BY payment_id ORDER BY _loaded_at DESC) = 1