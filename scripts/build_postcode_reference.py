"""
Build the postcode reference table used by the data generator.

Takes the cleaned CBS neighborhood data from my nl-housing-data-cleaning
project and collapses it to one row per 4-digit postcode (PC4).
"""

import pandas as pd
from pathlib import Path

SOURCE = (
    "https://raw.githubusercontent.com/alibaghdadi1368/"
    "nl-housing-data-cleaning/main/data/processed/nl_housing_clean.csv"
)

OUT = Path("generator/reference/postcodes.csv")

buurten = pd.read_csv(SOURCE)
print(f"Loaded {len(buurten):,} neighborhoods")

# ~100 buurten have no postcode in the CBS release
buurten = buurten.dropna(subset=["postcode"])
buurten["postcode"] = buurten["postcode"].astype(int).astype(str).str.zfill(4)
buurten["gm_code"] = "GM" + buurten["WijkenEnBuurten"].str[2:6]

# a PC4 can span several buurten (and rarely two municipalities)
# keep the municipality with the most residents in the postcode
by_pc4 = (
    buurten.sort_values("population", ascending=False)
    .groupby("postcode")
    .agg(
        municipality=("municipality", "first"),
        gm_code=("gm_code", "first"),
        population=("population", "sum"),
        urbanity_level=("urbanity_level", "median"),
        avg_woz_k_eur=("avg_woz_value_k_eur", "mean"),
    )
    .reset_index()
)

by_pc4["urbanity_level"] = (by_pc4["urbanity_level"] + 0.5).astype(int)
by_pc4["avg_woz_k_eur"] = by_pc4["avg_woz_k_eur"].round(1)
by_pc4["population"] = by_pc4["population"].round().astype(int)

OUT.parent.mkdir(parents=True, exist_ok=True)
by_pc4.to_csv(OUT, index=False)
print(f"Wrote {len(by_pc4):,} postcodes to {OUT}")
print(by_pc4.head())
