# Insurance Claims Lakehouse

Work in progress. A data platform for **Polder Verzekeringen**, a made-up
Dutch car insurer: daily policy extracts and real-time claim events land
in Snowflake, get modelled with dbt into Bronze / Silver / Gold layers,
and feed a Streamlit dashboard on loss ratio, claim handling times and
fraud signals.

Stack: Python · Kafka · AWS S3 · Snowflake · dbt · Airflow · Streamlit

See [docs/architecture.md](docs/architecture.md) for the design.

## Status

- [x] Synthetic source data (policies, premiums, claim events)
- [x] S3 + Snowflake Bronze
- [x] Kafka streaming
- [x] dbt Silver / Gold
- [x] Airflow
- [ ] Dashboard

## Run the generator

```bash
pip install -r requirements.txt
python scripts/build_postcode_reference.py   # once, needs internet
python -m generator backfill                 # history 2024-01-01 .. 2026-09-30
python -m generator daily --date 2026-10-01  # one more day
pytest -q
```