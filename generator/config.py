"""Knobs for the synthetic Polder Verzekeringen data.

Numbers are loosely based on the Dutch car insurance market: a few
hundred euros premium a year, roughly one claim per 7-8 policies a year
and a loss ratio around 70%. They don't need to be exact, they need to
produce believable patterns for the dashboard.
"""

from datetime import date
from pathlib import Path

SEED = 42

HISTORY_START = date(2024, 1, 1)
HISTORY_END = date(2026, 9, 30) #backfill stops here, daily runs continue after

N_CUSTOMERS = 12_000
SECOND_CAR_SHARE = 0.15
NEW_CUSTOMERS_PER_DAY = (8, 20) #min, max for daily runs

ROOT = Path(__file__).resolve().parents[1]
LANDING_DIR = ROOT / "data" / "landing"
POSTCODE_FILE = ROOT / "generator" / "reference" / "postcodes.csv"

# WA = third-party liability only, WA_PLUS adds theft/glass/storm,
# ALLRISK also covers damage to your own car
PRODUCTS = {
    "WA": {"base_premium": 480, "share": 0.40, "deductible": 0},
    "WA_PLUS": {"base_premium": 690, "share": 0.35, "deductible": 150},
    "ALLRISK": {"base_premium": 980, "share": 0.25, "deductible": 250},
}

# yearly frequency per policy and lognormal severity (median EUR, spread)
CLAIM_TYPES = {
    "third_party": {"freq": 0.045, "median": 3200, "sigma": 0.8, "products": {"WA", "WA_PLUS", "ALLRISK"}},
    "glass":       {"freq": 0.040, "median": 450, "sigma": 0.4, "products": {"WA_PLUS", "ALLRISK"}},
    "storm":       {"freq": 0.012, "median": 1600, "sigma": 0.7, "products": {"WA_PLUS", "ALLRISK"}},
    "theft":       {"freq": 0.006, "median": 9500, "sigma": 0.6, "products": {"WA_PLUS", "ALLRISK"}},
    "collision":   {"freq": 0.050, "median": 2800, "sigma": 0.9, "products": {"ALLRISK"}},
    "vandalism":   {"freq": 0.015, "median": 900, "sigma": 0.6, "products": {"ALLRISK"}},
}

# city drivers claim more often; level 1 = very strongly urban
URBANITY_RISK = {1: 1.35, 2: 1.2, 3: 1.0, 4: 0.9, 5: 0.8}
REJECTED_RATE = 0.12
FRAUD_POLICY_SHARE = 0.015 # policies that get a suspicious early claim

VEHICLES = [
    # make, model, fuel, catalog value range (EUR)
    ("Volkswagen", "Polo", "petrol", (19_000, 26_000)),
    ("Volkswagen", "Golf", "petrol", (28_000, 38_000)),
    ("Toyota", "Yaris", "hybrid", (21_000, 27_000)),
    ("Toyota", "Corolla", "hybrid", (30_000, 38_000)),
    ("Kia", "Niro", "electric", (36_000, 44_000)),
    ("Kia", "Picanto", "petrol", (14_000, 18_000)),
    ("Peugeot", "208", "petrol", (20_000, 27_000)),
    ("Renault", "Clio", "petrol", (19_000, 25_000)),
    ("Skoda", "Octavia", "diesel", (30_000, 40_000)),
    ("Ford", "Focus", "petrol", (25_000, 32_000)),
    ("Tesla", "Model 3", "electric", (42_000, 55_000)),
    ("Tesla", "Model Y", "electric", (45_000, 60_000)),
    ("Volvo", "XC40", "hybrid", (45_000, 58_000)),
    ("BMW", "3 Series", "petrol", (48_000, 65_000)),
]