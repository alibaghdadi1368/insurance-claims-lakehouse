-- picks the newest version of each customer and repairs the noise from make_messy.
-- One row per customer: the most recent version that has arrived so far.
-- Cleans the noise the source export adds (see generator/people.py make_messy).

with ranked as(
    SELECT 
        *,
        row_number() OVER(
            PARTITION BY customer_id
            ORDER BY updated_at DESC, _loaded_at DESC
        ) as rn 
    FROM {{ source('bronze', 'raw_customers') }}
)

SELECT
    customer_id,
    first_name,
    last_name,
    try_to_date(date_of_birth) as date_of_birth,
    lower(trim(email)) as email,
    -- '+31 6 12345678' and '0612345678' become the same number
    nullif(regexp_replace(REPLACE(phone, '+31 6', '06'), '[^0-9]', ''), '') as phone,
    -- '3821ab' -> '3821 AB'
    upper(substr(REPLACE(postcode, ' ', ''), 1, 4) || ' ' || substr(REPLACE(postcode, ' ', ''), 5, 2)) as postcode,
    substr(postcode, 1, 4) as pc4,
    city,
    try_to_date(customer_since) as customer_since,
    try_to_date(updated_at)::timestamp_ntz as update_at
FROM ranked
where rn = 1