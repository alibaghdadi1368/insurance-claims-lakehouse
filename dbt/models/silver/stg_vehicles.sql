SELECT DISTINCT
    vehicle_id,
    customer_id,
    license_plate,
    make,
    model,
    fuel_type,
    try_to_number(build_year) as build_year,
    try_to_number(catalog_value_eur) as catalog_value_eur
from {{ source('bronze', 'raw_vehicles') }}