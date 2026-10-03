select
    vehicle_id,
    customer_id,
    license_plate,
    make,
    model,
    fuel_type,
    build_year,
    catalog_value_eur
from {{ ref('stg_vehicles') }}
