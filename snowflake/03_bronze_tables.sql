-- 03_bronze_tables.sql
-- Bronze keeps data exactly as delivered: every CSV column is a string,
-- every event is the raw JSON. Typing and cleaning happen in Silver (dbt).

USE ROLE TRANSFORMER;
USE WAREHOUSE WH_PIPELINE;
USE SCHEMA INSURANCE.BRONZE;

CREATE TABLE IF NOT EXISTS RAW_CUSTOMERS (
    customer_id     VARCHAR,
    first_name      VARCHAR,
    last_name       VARCHAR,
    date_of_birth   VARCHAR,
    email           VARCHAR,
    phone           VARCHAR,
    postcode        VARCHAR,
    city            VARCHAR,
    customer_since  VARCHAR,
    updated_at      VARCHAR,
    _source_file    VARCHAR,
    _loaded_at      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS RAW_VEHICLES (
    vehicle_id        VARCHAR,
    customer_id       VARCHAR,
    license_plate     VARCHAR,
    make              VARCHAR,
    model             VARCHAR,
    fuel_type         VARCHAR,
    build_year        VARCHAR,
    catalog_value_eur VARCHAR,
    _source_file      VARCHAR,
    _loaded_at        TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS RAW_POLICIES (
    policy_id          VARCHAR,
    customer_id        VARCHAR,
    vehicle_id         VARCHAR,
    product_code       VARCHAR,
    start_date         VARCHAR,
    end_date           VARCHAR,
    status             VARCHAR,
    annual_premium_eur VARCHAR,
    deductible_eur     VARCHAR,
    no_claim_years     VARCHAR,
    updated_at         VARCHAR,
    _source_file       VARCHAR,
    _loaded_at         TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS RAW_PREMIUMS (
    payment_id     VARCHAR,
    policy_id      VARCHAR,
    due_date       VARCHAR,
    amount_eur     VARCHAR,
    paid_date      VARCHAR,
    payment_method VARCHAR,
    _source_file   VARCHAR,
    _loaded_at     TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS RAW_CLAIM_EVENTS (
    event        VARIANT,
    _source_file VARCHAR,
    _loaded_at   TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS RAW_POSTCODES (
    postcode       VARCHAR,
    municipality   VARCHAR,
    gm_code        VARCHAR,
    population     VARCHAR,
    urbanity_level VARCHAR,
    avg_woz_k_eur  VARCHAR,
    _source_file   VARCHAR,
    _loaded_at     TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);
