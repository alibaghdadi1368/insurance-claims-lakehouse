"""
With Snowflake settings in .env it reads the live Gold tables; without them
it reads the Parquet snapshot in dashboard/demo_data/.
"""
import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

HERE = Path(__file__).parent
DEMO = HERE / "demo_data"

# read Snowflake settings from the repo's .env (no file on Streamlit Cloud: demo mode)
load_dotenv(HERE.parent / ".env")

def live_mode() -> bool:
    return bool(os.getenv("SNOWFLAKE_ACCOUNT")) and os.getenv("DEMO_MODE") != "1"

@st.cache_data(ttl=600) 
def table(name: str) -> pd.DataFrame:
    if live_mode():
        import sys
        sys.path.insert(0, str(HERE.parent))
        from pipeline.settings import snowflake_connect
        with snowflake_connect() as conn:
            df = pd.read_sql(f"select * from GOLD.{name.upper()}", conn)
        df.columns = [c.lower() for c in df.columns]
    else:
        df = pd.read_parquet(DEMO / f"{name}.parquet")

    # dates arrive from both sources(make real dates)
    for col in df.columns:
        if col == "month" or col.endswith("_date"):
            df[col] = pd.to_datetime(df[col])
    return df

@st.cache_data
def municipalities() -> dict:
    return json.loads((HERE / "assets" / "gemeente_2025.geojson").read_text(encoding="utf-8"))
 