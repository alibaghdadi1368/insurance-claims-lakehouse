"""
Save the Gold tables the dashboard needs as small Parquet files.

    python -m pipeline.export_demo

The files land in dashboard/demo_data/ and are committed to Git, so the
public demo keeps working after the Snowflake trial has ended.
"""
import pandas as pd
from pipeline.settings import ROOT, snowflake_connect

OUT = ROOT / "dashboard" / "demo_data"
TABLES = [
    "MART_LOSS_RATIO_MONTHLY",
    "MART_CLAIMS_SLA",
    "MART_FRAUD_SIGNALS",
    "MART_REGION_RISK",
    "FCT_CLAIMS",
]

def export():
    OUT.mkdir(parents=True, exist_ok=True)
    with snowflake_connect() as conn:
        for table in TABLES:
            df = pd.read_sql(f"select * from GOLD.{table}", conn)
            df.columns = [c.lower() for c in df.columns]
            df.to_parquet(OUT / f"{table.lower()}.parquet", index=False)
            print(f"  {table:<24} {len(df):>6,} rows")

if __name__ == "__main__":
    export()