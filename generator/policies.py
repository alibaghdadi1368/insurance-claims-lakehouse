"""Policies and monthly premium payments."""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from generator import config

AVG_POLICY_YEARS = 9  # how long a customer stays on average


def age_factor(age: int) -> float:
    if age < 25:
        return 1.6
    if age < 30:
        return 1.2
    if age >= 75:
        return 1.15
    return 1.0


def annual_premium(product, age, urbanity, catalog_value, no_claim_years):
    premium = config.PRODUCTS[product]["base_premium"] * age_factor(age)
    premium *= config.URBANITY_RISK[urbanity] ** 0.8
    if product != "WA":
        # own-damage cover scales with what the car is worth
        premium *= (catalog_value / 30_000) ** 0.4
    premium *= 1 - min(no_claim_years, 15) * 0.03
    return round(premium, 2)


def make_policies(vehicles, customers, postcodes, first_id, rng, latest_start):
    cust = customers.drop_duplicates("customer_id").set_index("customer_id")
    urb = postcodes.set_index("postcode")["urbanity_level"]

    names = list(config.PRODUCTS)
    shares = [config.PRODUCTS[p]["share"] for p in names]

    rows = []
    seen_owner = set()
    for i, v in enumerate(vehicles.itertuples(index=False)):
        c = cust.loc[v.customer_id]
        since = c["customer_since"]
        # a second car is insured some time after the first one
        if v.customer_id in seen_owner:
            gap = (latest_start - since).days
            start = since + timedelta(days=int(rng.integers(0, max(gap, 1))))
        else:
            start = since
        seen_owner.add(v.customer_id)

        product = rng.choice(names, p=shares)
        # newer cars are more often fully insured
        if v.build_year >= 2023 and rng.random() < 0.4:
            product = "ALLRISK"

        age = (start - c["date_of_birth"]).days // 365
        ncy = int(np.clip(rng.integers(0, max(age - 17, 1)), 0, 20))
        urbanity = int(urb.get(c["postcode"][:4], 3))

        lifetime = timedelta(days=int(rng.exponential(AVG_POLICY_YEARS * 365)))
        end = start + lifetime
        cancelled = end <= latest_start

        rows.append({
            "policy_id": f"POL-{first_id + i:06d}",
            "customer_id": v.customer_id,
            "vehicle_id": v.vehicle_id,
            "product_code": product,
            "start_date": start,
            "end_date": end if cancelled else None,
            "status": "cancelled" if cancelled else "active",
            "annual_premium_eur": annual_premium(product, age, urbanity, v.catalog_value_eur, ncy),
            "deductible_eur": config.PRODUCTS[product]["deductible"],
            "no_claim_years": ncy,
            "updated_at": end if cancelled else start,
        })
    return pd.DataFrame(rows)


def due_day(start: date) -> int:
    # collect on the start day, but never on the 29th-31st
    return min(start.day, 28)


def make_premiums(policies, period_start, period_end, rng, first_id=1):
    rows = []
    for p in policies.itertuples(index=False):
        first = max(p.start_date, period_start)
        last = min(p.end_date or period_end, period_end)
        if first > last:
            continue
        months = pd.date_range(first.replace(day=1), last, freq="MS")
        monthly = round(p.annual_premium_eur / 12, 2)
        for m in months:
            due = m.date().replace(day=due_day(p.start_date))
            if first <= due <= last:
                rows.append((p.policy_id, due, monthly))

    df = pd.DataFrame(rows, columns=["policy_id", "due_date", "amount_eur"])
    df = df.sort_values(["due_date", "policy_id"]).reset_index(drop=True)
    df.insert(0, "payment_id", [f"PAY-{first_id + i:08d}" for i in range(len(df))])
    return add_payment_outcome(df, period_end, rng)


def add_payment_outcome(df, as_of, rng):
    n = len(df)
    roll = rng.random(n)
    delay = np.where(roll < 0.04, rng.integers(15, 61, n), rng.integers(0, 6, n))
    paid = [d + timedelta(days=int(x)) for d, x in zip(df["due_date"], delay)]

    unpaid = roll > 0.985
    df["paid_date"] = [None if u or p > as_of else p for u, p in zip(unpaid, paid)]
    df["payment_method"] = rng.choice(["direct_debit", "ideal", "bank_transfer"], n, p=[0.8, 0.12, 0.08])
    return df
