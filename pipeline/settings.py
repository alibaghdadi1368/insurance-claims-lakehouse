"""Reads connection settings from .env so no secret ever sits in the code."""
import json
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value

def last_business_day() -> str:
    """The last day the generator produced, e.g. '2026-10-03'."""
    return json.loads((ROOT / "data" / "state" / "meta.json").read_text())["last_run"]

def snowflake_connect():
    import snowflake.connector

    return snowflake.connector.connect(
        account=env("SNOWFLAKE_ACCOUNT"),
        user=env("SNOWFLAKE_USER"),
        password=env("SNOWFLAKE_PASSWORD"),
        role=env("SNOWFLAKE_ROLE"),
        warehouse=env("SNOWFLAKE_WAREHOUSE"),
        database="INSURANCE",

)