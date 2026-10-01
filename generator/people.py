"""Customers and their cars."""

from datetime import date, timedelta
import numpy as np
import pandas as pd
from generator import config

# Dutch postcodes never use these letter pairs
BANNED_PC_LETTERS = {"SA", "SD", "SS"}
# Dutch plates skip vowels (and, C, Q, W, M, Y) so they can't spell words
PLATE_LETTERS = list("BDFGHJKLNPRSTVXZ")

def load_postcodes() -> pd.DataFrame:
    pcs = pd.read_csv(config.POSTCODE_FILE, dtype={"postcode": str})
    pcs["weight"] = pcs["population"] / pcs["population"].sum()
    return pcs

def _random_dates(rng, start: date, end: date, n: int) -> list[date]:
    span = (end - start).days
    return [start + timedelta(days=int(d)) for d in rng.integers(0, span + 1, n)]

def _full_postcode(rng, pc4: str) -> str:
    while True:
        letters = "".join(rng.choice(list("ABCDEFGHJKLMNPRSTVWXZ"), 2))
        if letters not in BANNED_PC_LETTERS:
            return f"{pc4} {letters}"

def _plate(rng) -> str:
    # one of the current sidecode formats, e.g. GX-123-B
    l1 = "".join(rng.choice(PLATE_LETTERS, 2))
    l2 = rng.choice(PLATE_LETTERS)
    return f"{l1}-{rng.integers(100, 1000)}-{l2}"

def make_customers(n, first_id, since_start, since_end, rng, fake, postcode):
    pc_rows = postcode.sample(n, replace=True, weights="weight", random_state=rng)
    since = _random_dates(rng, since_start, since_end, n)
    # adult drivers, most of them between 30 and 60
    ages = np.clip(rng.normal(46, 14, n), 18, 88).astype(int)
    birth = [s - timedelta(days=int(a * 365.25 + rng.integers(0, 365))) for s, a in zip(since, age)]

    rows = []
    for i in range(n):
        first, last = fake.first_name(), fake.last_name()
        email_name = f"{first}.{last}".lower().replace(" ", "").replace("'", "")
        rows.append({
            "customer_id": f"CUS-{first_id + i:06d}",
            "first_name": first,
            "last_name": last,
            "date_of_birth": birth[i],
            "email": f"{email_name}@{fake.free_email_domain()}",
            "phone": "06" + "".join(str(d) for d in rng.integers(0, 10, 8)),
            "postcode": _full_postcode(rng, pc_rows["postcode"].iat[i]),
            "city": pc_rows["municipality"].iat[i],
            "customer_since": since[i],
            "updated_at": since[i]
        })
        return pd.DataFrame(rows)

def make_vehicles(customers, first_id, rng):
    owners = list(customers["customer_id"])
    # some households insure a second car
    second = customers.sample(frac=config.SECOND_CAR_SHARE, random_state=rng)["customer_id"]
    owners += list(second)
    picks = rng.integers(0, len(config.VEHICLES), len(owners))
    rows = []
    for i, (owner, pick) in enumerate(zip(owners, picks)):
        make, model, fuel, (lo, hi) = config.VEHICLES[pick]
        build_year = int(rng.integers(2010, 2027))
        rows.append({
            "vehicle_id": f"VEH-{first_id + i:06d}",
            "customer_id": owner,
            "license_plate": _plate(rng),
            "make": make,
            "model": model,
            "fuel_type": fuel,
            "build_year": build_year,
            "catalog_value_eur": int(rng.integers(lo, hi) // 100 * 100),
        })
    return pd.DataFrame(rows)

def make_messy(customers, rng):
    """Real exports are never clean. Add the kind of noise Silver has to fix."""
    df = customers.copy()
    n = len(df)
    # postcodes typed without the space and in lower case
    idx = rng.choice(n, size=int(n * 0.03), replace=False)
    df.loc[df.index[idx], "postcode"] = df["postcode"].iloc[idx].str.replace(" ", "").str.lower()
    # emails in capitals from an old web form
    idx = rng.choice(n, size=int(n * 0.02), replace=False)
    df.loc[df.index[idx], "email"] = df["email"].iloc[idx].str.upper()
    # international phone format
    idx = rng.choice(n, size=int(n * 0.10), replace=False)
    df.loc[df.index[idx], "phone"] = "+31 6 " + df["phone"].iloc[idx].str[2:]
    # a few missing phone format
    idx = rng.choice(n, size=int(n * 0.01), replace=False)
    df.loc[df.index[idx], "phone"] = None
    # the export job sometimes writes a row twice
    dupes = df.sample(frac=0.005, random_state=rng)
    return pd.concat([df, dupes]).sort_values("customer_id").reset_index(drop=True)
