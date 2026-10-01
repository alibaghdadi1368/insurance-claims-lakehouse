# Architecture

```mermaid
flowchart LR
    subgraph sources[Source systems - simulated]
        GEN[Policy admin export<br/>Python generator]
        CLM[Claims portal events<br/>Kafka producer]
        CBS[CBS postcode reference]
    end

    GEN -- daily CSV --> S3[(S3 landing bucket)]
    S3 -- COPY INTO --> BRONZE
    CLM --> KAFKA[[Kafka topic<br/>claim-events]] --> CONS[Python consumer] --> BRONZE
    CBS --> BRONZE

    subgraph snowflake[Snowflake]
        BRONZE[(BRONZE<br/>raw, as delivered)]
        SILVER[(SILVER<br/>clean, typed, SCD2)]
        GOLD[(GOLD<br/>star schema + marts)]
        BRONZE -- dbt --> SILVER -- dbt --> GOLD
    end

    GOLD --> APP[Streamlit dashboard]
    AIRFLOW{{Airflow daily DAG}} -.orchestrates.-> GEN & S3 & BRONZE & SILVER
```

| Layer | What lives there | Rule |
|---|---|---|
| Bronze | Files and events exactly as received, plus load metadata | Never updated, only appended |
| Silver | Typed, deduplicated, standardised tables; policy history (SCD2) | One row per business entity version |
| Gold | Facts, dimensions and business marts | Only what the dashboard and analysts need |