-- uses qualify, Snowflake's shortcut for filtering on a window function without a subquery.
SELECT
    lpad(postcode, 4, '0') as pc4,
    municipality,
    gm_code,
    try_to_number(population) as population,
    try_to_number(urbanity_level) as urbanity_level,
    try_to_decimal(avg_woz_k_eur, 8, 1) as avg_woz_k_eur
from {{ source('bronze', 'raw_postcodes') }}
qualify row_number() OVER(PARTITION BY postcode order by _loaded_at DESC) = 1