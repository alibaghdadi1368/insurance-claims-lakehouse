"""
Load new files from the S3 stage into the Bronze tables.

    python -m pipeline.bronze_load

COPY INTO remembers which files it already loaded (for 64 days), so running
this twice never creates duplicates. That makes it safe to retry.
"""
from pipeline.settings import snowflake_connect

# table -> (folder in the stage, file format, columns in file order)
SOURCES = {
    "RAW_CUSTOMERS": ("customers/", "FF_CSV_SEMICOLON",
                      "customer_id, first_name, last_name, date_of_birth, email, phone, "
                      "postcode, city, customer_since, updated_at"),
    "RAW_VEHICLES": ("vehicles/", "FF_CSV_SEMICOLON",
                     "vehicle_id, customer_id, license_plate, make, model, fuel_type, "
                     "build_year, catalog_value_eur"),
    "RAW_POLICIES": ("policies/", "FF_CSV_SEMICOLON",
                     "policy_id, customer_id, vehicle_id, product_code, start_date, end_date, "
                     "status, annual_premium_eur, deductible_eur, no_claim_years, updated_at"),
    "RAW_PREMIUMS": ("premiums/", "FF_CSV_SEMICOLON",
                     "payment_id, policy_id, due_date, amount_eur, paid_date, payment_method"),
    "RAW_POSTCODES": ("reference/", "FF_CSV_COMMA",
                      "postcode, municipality, gm_code, population, urbanity_level, avg_woz_k_eur"),
    "RAW_CLAIM_EVENTS": ("claim_events/", "FF_JSON", "event"),
}

def copy_sql(table, folder, file_format, columns):
    n = len(columns.split(","))
    picks = ", ".join(f"${i}" for i in range(1, n + 1))
    return (
        f"COPY INTO BRONZE.{table} ({columns}, _source_file)\n"
        f"FROM (SELECT {picks}, METADATA$FILENAME FROM @BRONZE.LANDING/{folder})\n"
        f"FILE_FORMAT = (FORMAT_NAME = 'BRONZE.{file_format}')\n"
        f"ON_ERROR = 'ABORT_STATEMENT'"
    )

def load():
    with snowflake_connect() as conn:
        cur = conn.cursor()
        for table, (folder, fmt, columns) in SOURCES.items():
            cur.execute(copy_sql(table, folder, fmt, columns))
            # one result row per loaded file; a single status row when nothing was new
            results = [r for r in cur.fetchall() if len(r) > 3]
            rows = sum(r[3] for r in results)
            print(f"    {table:<18} {len(results):>3} new files {rows:>9,} rows")

if __name__ == "__main__":
    load()