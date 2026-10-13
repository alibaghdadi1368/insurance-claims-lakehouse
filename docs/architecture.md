# Architecture

```mermaid
flowchart LR
    subgraph sources[Source systems - simulated]
        GEN[Policy admin export<br/>Python generator]
        CLM[Claims portal events<br/>Kafka producer]
        CBS[CBS postcode reference<br/>CSV]
    end

    GEN -- daily CSV --> S3[(S3 landing bucket)]
    CBS -- reference CSV --> S3
    CLM --> KAFKA[[Kafka topic<br/>claim-events]] --> CONS[Python consumer] -- JSON files --> S3
    S3 -- COPY INTO --> BRONZE

    subgraph snowflake[Snowflake]
        BRONZE[(BRONZE<br/>raw, as delivered)]
        SILVER[(SILVER<br/>clean, typed, SCD2)]
        GOLD[(GOLD<br/>star schema + marts)]
        BRONZE -- dbt --> SILVER -- dbt --> GOLD
    end

    GOLD -- live query (local) --> APP[Streamlit dashboard]
    GOLD -. Parquet export<br/>for the public demo .-> APP
    AIRFLOW{{Airflow daily DAG<br/>orchestrates every step}} -.-> GEN & CLM & CONS & S3 & BRONZE & SILVER & GOLD
```

| Layer | What lives there | Rule |
|---|---|---|
| Bronze | Files and events exactly as received, plus load metadata | Never updated, only appended |
| Silver | Typed, deduplicated, standardised tables; policy history (SCD2) | One row per business entity version |
| Gold | Facts, dimensions and business marts | Only what the dashboard and analysts need |