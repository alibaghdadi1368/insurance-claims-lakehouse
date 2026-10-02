"""
Generate source data for Polder Verzekeringen.

    python -m generator backfill                  # history up to config.HISTORY_END
    python -m generator daily --date 2026-10-01   # one more business day

Batch extracts go to data/landing/<entity>/ as semicolon-separated CSV,
the way the (imaginary) policy admin system exports them. Claim events of
a daily run go to data/outbox/; the Kafka producer picks them up there.
"""

import argparse
import json
import shutil
from datetime import date, timedelta
import numpy as np
import pandas as pd
from faker import Faker
from generator import claims, config, people, policies

OUTBOX_DIR = config.ROOT / "data" / "outbox"


# ---------- writing ----------

def write_csv(df, entity, day):
    folder = config.LANDING_DIR / entity
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{entity}_{day.isoformat()}.csv"
    df.to_csv(path, sep=";", index=False)
    print(f"  {entity:<10} {len(df):>8,} rows -> {path.relative_to(config.ROOT)}")


def write_jsonl(events, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for e in sorted(events, key=lambda e: e["event_ts"]):
            f.write(json.dumps(e) + "\n")
    print(f"  {'events':<10} {len(events):>8,} rows -> {path.relative_to(config.ROOT)}")


def read_jsonl(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# ---------- state between runs ----------

def save_state(customers, vehicles, pols, pending, meta):
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    customers.to_parquet(config.STATE_DIR / "customers.parquet", index=False)
    vehicles.to_parquet(config.STATE_DIR / "vehicles.parquet", index=False)
    pols.to_parquet(config.STATE_DIR / "policies.parquet", index=False)
    write_jsonl(pending, config.STATE_DIR / "pending_events.jsonl")
    (config.STATE_DIR / "meta.json").write_text(json.dumps(meta, indent=2))


def load_state():
    meta_file = config.STATE_DIR / "meta.json"
    if not meta_file.exists():
        raise SystemExit("No state found. Run `python -m generator backfill` first.")

    def dates(df, cols):
        for c in cols:
            df[c] = pd.to_datetime(df[c]).dt.date
            df[c] = df[c].astype(object).where(df[c].notna(), None)
        return df

    customers = dates(pd.read_parquet(config.STATE_DIR / "customers.parquet"),
                      ["date_of_birth", "customer_since", "updated_at"])
    vehicles = pd.read_parquet(config.STATE_DIR / "vehicles.parquet")
    pols = dates(pd.read_parquet(config.STATE_DIR / "policies.parquet"),
                 ["start_date", "end_date", "updated_at"])
    pending = read_jsonl(config.STATE_DIR / "pending_events.jsonl")
    meta = json.loads(meta_file.read_text())
    return customers, vehicles, pols, pending, meta


def claim_context(pols, customers, vehicles, postcodes):
    """Per policy: urbanity of the address, driver age at start, car value."""
    urb = postcodes.set_index("postcode")["urbanity_level"]
    ctx = (pols[["policy_id", "customer_id", "vehicle_id", "start_date"]]
           .merge(customers[["customer_id", "date_of_birth", "postcode"]], on="customer_id")
           .merge(vehicles[["vehicle_id", "catalog_value_eur"]], on="vehicle_id"))
    ctx["urbanity"] = ctx["postcode"].str[:4].map(urb).fillna(3).astype(int)
    ctx["driver_age"] = [(s - b).days // 365 for s, b in zip(ctx["start_date"], ctx["date_of_birth"])]
    ctx["vehicle_value"] = ctx["catalog_value_eur"]
    return ctx.set_index("policy_id")


# ---------- the two modes ----------

def backfill():
    rng = np.random.default_rng(config.SEED)
    fake = Faker("nl_NL")
    fake.seed_instance(config.SEED)
    postcodes = people.load_postcodes()
    end = config.HISTORY_END

    # start clean, a backfill replaces everything
    for folder in (config.LANDING_DIR, config.STATE_DIR, OUTBOX_DIR):
        shutil.rmtree(folder, ignore_errors=True)

    print(f"Backfill {config.HISTORY_START} .. {end}")
    customers = people.make_customers(config.N_CUSTOMERS, 1, date(2016, 1, 1), end, rng, fake, postcodes)
    vehicles = people.make_vehicles(customers, 1, rng)
    pols = policies.make_policies(vehicles, customers, postcodes, 1, rng, latest_start=end)
    premiums = policies.make_premiums(pols, config.HISTORY_START, end, rng)

    ctx = claim_context(pols, customers, vehicles, postcodes)
    events, next_claim = claims.claims_for_period(pols, ctx, config.HISTORY_START, end, rng, 1)
    fishy, next_claim = claims.suspicious_claims(pols, ctx, config.HISTORY_START, end, rng, next_claim)
    history, pending = claims.split_by_day(events + fishy, end)
    history = claims.add_duplicates(history, rng)

    write_csv(people.make_messy(customers, rng), "customers", end)
    write_csv(vehicles, "vehicles", end)
    write_csv(pols, "policies", end)
    write_csv(premiums, "premiums", end)
    write_jsonl(history, config.LANDING_DIR / "claim_events" / f"claim_events_backfill_{end}.jsonl")

    meta = {
        "last_run": end.isoformat(),
        "next_customer": len(customers) + 1,
        "next_vehicle": len(vehicles) + 1,
        "next_policy": len(pols) + 1,
        "next_payment": len(premiums) + 1,
        "next_claim": next_claim,
    }
    save_state(customers, vehicles, pols, pending, meta)


def daily(day: date):
    customers, vehicles, pols, pending, meta = load_state()
    last = date.fromisoformat(meta["last_run"])
    if day != last + timedelta(days=1):
        raise SystemExit(f"Last run was {last}; days must be generated in order (next is {last + timedelta(days=1)}).")

    # seeded per day, so re-running the same day gives the same output
    rng = np.random.default_rng([config.SEED, day.toordinal()])
    fake = Faker("nl_NL")
    fake.seed_instance(config.SEED + day.toordinal())
    postcodes = people.load_postcodes()
    print(f"Daily run for {day}")

    # new business
    n_new = int(rng.integers(*config.NEW_CUSTOMERS_PER_DAY))
    new_cust = people.make_customers(n_new, meta["next_customer"], day, day, rng, fake, postcodes)
    new_veh = people.make_vehicles(new_cust, meta["next_vehicle"], rng)
    new_pol = policies.make_policies(new_veh, new_cust, postcodes, meta["next_policy"], rng, latest_start=day)

    # a few existing customers move house (a type 2 change downstream)
    movers = customers.sample(n=int(rng.poisson(len(customers) * 0.0004)), random_state=rng).index
    for i in movers:
        pc = postcodes.sample(1, weights="weight", random_state=rng).iloc[0]
        customers.loc[i, ["postcode", "city", "updated_at"]] = [
            people._full_postcode(rng, pc["postcode"]), pc["municipality"], day]

    active = (pols["status"] == "active") & (pols["start_date"] < day)

    # cancellations
    leaving = active & (rng.random(len(pols)) < 1 / (policies.AVG_POLICY_YEARS * 365))
    pols.loc[leaving, ["status", "end_date", "updated_at"]] = ["cancelled", day, day]

    # yearly renewal: premium indexed, one more claim-free year
    renew = active & ~leaving & pols["start_date"].map(lambda s: (s.month, s.day) == (day.month, day.day))
    pols.loc[renew, "annual_premium_eur"] = (pols.loc[renew, "annual_premium_eur"] * 1.035).round(2)
    pols.loc[renew, "no_claim_years"] += 1
    pols.loc[renew, "updated_at"] = day

    changed_pol = pd.concat([pols[leaving | renew], new_pol])
    changed_cust = pd.concat([customers.loc[movers], new_cust])

    # premiums collected today
    billing = pols[active & ~leaving]
    billing = billing[billing["start_date"].map(policies.due_day) == day.day]
    premiums = pd.DataFrame({
        "payment_id": [f"PAY-{meta['next_payment'] + i:08d}" for i in range(len(billing))],
        "policy_id": billing["policy_id"].values,
        "due_date": day,
        "amount_eur": (billing["annual_premium_eur"] / 12).round(2).values,
    })
    method = rng.choice(["direct_debit", "ideal", "bank_transfer"], len(premiums), p=[0.8, 0.12, 0.08])
    collected = (method == "direct_debit") & (rng.random(len(premiums)) > 0.03)
    premiums["paid_date"] = [day if ok else None for ok in collected]
    premiums["payment_method"] = method

    # claims: new ones today, plus steps of older claims that fall on today
    customers = pd.concat([customers, new_cust], ignore_index=True)
    vehicles = pd.concat([vehicles, new_veh], ignore_index=True)
    pols = pd.concat([pols[~pols["policy_id"].isin(new_pol["policy_id"])], new_pol], ignore_index=True)
    ctx = claim_context(pols, customers, vehicles, postcodes)

    on_risk = pols[(pols["status"] == "active") & (pols["start_date"] <= day)]
    events, next_claim = claims.claims_for_period(on_risk, ctx, day, day, rng, meta["next_claim"])

    # now and then a policy that started two weeks ago reports a big theft
    two_weeks = on_risk[(on_risk["start_date"] == day - timedelta(days=14)) & (on_risk["product_code"] != "WA")]
    for p in two_weeks.itertuples(index=False):
        if rng.random() < 0.05:
            cid = f"CLM-{next_claim:07d}"
            next_claim += 1
            events += claims.plan_claim(rng, cid, p, ctx.loc[p.policy_id, "vehicle_value"],
                                        day - timedelta(days=int(rng.integers(8, 14))), "theft", suspicious=True)

    today, pending = claims.split_by_day(pending + events, day)
    today = claims.add_duplicates(today, rng)

    write_csv(people.make_messy(changed_cust, rng), "customers", day)
    write_csv(new_veh, "vehicles", day)
    write_csv(changed_pol, "policies", day)
    write_csv(premiums, "premiums", day)
    write_jsonl(today, OUTBOX_DIR / f"claim_events_{day}.jsonl")

    meta.update({
        "last_run": day.isoformat(),
        "next_customer": meta["next_customer"] + len(new_cust),
        "next_vehicle": meta["next_vehicle"] + len(new_veh),
        "next_policy": meta["next_policy"] + len(new_pol),
        "next_payment": meta["next_payment"] + len(premiums),
        "next_claim": next_claim,
    })
    save_state(customers, vehicles, pols, pending, meta)


def main():
    parser = argparse.ArgumentParser(description="Polder Verzekeringen data generator")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("backfill", help="generate the full history")
    d = sub.add_parser("daily", help="generate one business day")
    d.add_argument("--date", required=True, type=date.fromisoformat)
    args = parser.parse_args()

    if args.mode == "backfill":
        backfill()
    else:
        daily(args.date)


if __name__ == "__main__":
    main()