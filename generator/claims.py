"""Claims and the events the claims system emits for them.

A claim is planned in one go when it is reported: we decide up front when
it will be assessed, approved or rejected and paid. Each step becomes an
event with its own timestamp. Events dated in the future are kept as
"pending" and released by later daily runs, so a claim reported today
gets its payment event a few weeks later, like in real life.
"""

import uuid
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

from generator import config

CHANNELS = ["app", "phone", "broker", "web"]


def _event_id(rng) -> str:
    return str(uuid.UUID(bytes=rng.bytes(16), version=4))


def _ts(rng, day: date, office_hours=True) -> str:
    hour = int(rng.integers(8, 18)) if office_hours else int(rng.integers(0, 24))
    t = time(hour, int(rng.integers(0, 60)), int(rng.integers(0, 60)))
    return datetime.combine(day, t).isoformat() + "Z"


def _event(rng, kind, day, claim_id, policy_id, payload, office_hours=True):
    return {
        "event_id": _event_id(rng),
        "event_type": kind,
        "event_ts": _ts(rng, day, office_hours),
        "schema_version": 1,
        "claim_id": claim_id,
        "policy_id": policy_id,
        "source": "claims-portal",
        "payload": payload,
    }


def plan_claim(rng, claim_id, policy, vehicle_value, incident: date, claim_type, suspicious=False):
    """Return all lifecycle events for one claim, dated from report to payment."""
    spec = config.CLAIM_TYPES[claim_type]
    reported = incident + timedelta(days=int(rng.geometric(0.45) - 1))
    if suspicious:
        reported = incident + timedelta(days=int(rng.integers(8, 21)))  # reported late

    if suspicious:
        claimed = vehicle_value * rng.uniform(0.85, 1.0)
    else:
        claimed = rng.lognormal(np.log(spec["median"]), spec["sigma"])
        if claim_type in ("theft", "collision"):
            claimed = min(claimed, vehicle_value)
    claimed = round(float(claimed), 2)

    events = [_event(rng, "CLAIM_REPORTED", reported, claim_id, policy.policy_id, {
        "incident_date": incident.isoformat(),
        "claim_type": claim_type,
        "claimed_amount": claimed,
        "channel": str(rng.choice(CHANNELS, p=[0.45, 0.25, 0.2, 0.1])),
    }, office_hours=False)]

    # bigger claims need an expert visit and take longer
    wait = rng.integers(5, 25) if claimed > 5000 else rng.integers(1, 10)
    assessed_on = reported + timedelta(days=int(wait))
    assessed = round(claimed * float(rng.uniform(0.7, 1.0)), 2)
    events.append(_event(rng, "CLAIM_ASSESSED", assessed_on, claim_id, policy.policy_id, {
        "assessed_amount": assessed,
        "assessor_id": f"ASR-{int(rng.integers(1, 40)):03d}",
    }))

    decided_on = assessed_on + timedelta(days=int(rng.integers(1, 8)))
    deductible = policy.deductible_eur
    reject_p = 0.45 if suspicious else config.REJECTION_RATE

    if assessed <= deductible:
        reason = "below_deductible"
    elif rng.random() < reject_p:
        reason = "suspected_fraud" if suspicious else str(rng.choice(["not_covered", "insufficient_evidence"]))
    else:
        reason = None

    if reason:
        events.append(_event(rng, "CLAIM_REJECTED", decided_on, claim_id, policy.policy_id, {"reason": reason}))
        return events

    approved = assessed
    events.append(_event(rng, "CLAIM_APPROVED", decided_on, claim_id, policy.policy_id, {
        "approved_amount": approved,
    }))
    paid_on = decided_on + timedelta(days=int(rng.integers(2, 15)))
    events.append(_event(rng, "CLAIM_PAID", paid_on, claim_id, policy.policy_id, {
        "paid_amount": round(approved - deductible, 2),
        "payment_reference": f"PV{paid_on:%Y%m%d}{int(rng.integers(10000, 99999))}",
    }))
    return events


def daily_claim_rate(policy, urbanity, age) -> dict:
    risk = config.URBANITY_RISK[urbanity] * (1.8 if age < 25 else 1.0)
    return {
        kind: spec["freq"] * risk / 365
        for kind, spec in config.CLAIM_TYPES.items()
        if policy.product_code in spec["products"]
    }


def claims_for_period(policies, context, start, end, rng, first_id):
    """Plan every claim with an incident between start and end (inclusive).

    context: DataFrame indexed by policy_id with urbanity, driver_age, vehicle_value.
    """
    events, next_id = [], first_id
    for p in policies.itertuples(index=False):
        first = max(p.start_date, start)
        last = min(p.end_date or end, end)
        days = (last - first).days + 1
        if days <= 0:
            continue
        ctx = context.loc[p.policy_id]
        rates = daily_claim_rate(p, int(ctx["urbanity"]), int(ctx["driver_age"]))
        for kind, rate in rates.items():
            for _ in range(rng.poisson(rate * days)):
                incident = first + timedelta(days=int(rng.integers(0, days)))
                cid = f"CLM-{next_id:07d}"
                next_id += 1
                events += plan_claim(rng, cid, p, ctx["vehicle_value"], incident, kind)
    return events, next_id


def suspicious_claims(policies, context, start, end, rng, first_id):
    """A small set of new policies get a large claim within weeks of starting."""
    fresh = policies[(policies["start_date"] >= start) & (policies["start_date"] <= end - timedelta(days=30))]
    fresh = fresh[fresh["product_code"] != "WA"]
    n = min(round(len(policies) * config.FRAUD_POLICY_SHARE), len(fresh))
    picked = fresh.sample(n, random_state=rng)

    events, next_id = [], first_id
    for p in picked.itertuples(index=False):
        incident = p.start_date + timedelta(days=int(rng.integers(3, 25)))
        kind = str(rng.choice(["theft", "collision"])) if p.product_code == "ALLRISK" else "theft"
        cid = f"CLM-{next_id:07d}"
        next_id += 1
        events += plan_claim(rng, cid, p, context.loc[p.policy_id, "vehicle_value"], incident, kind, suspicious=True)
    return events, next_id


def add_duplicates(events, rng, share=0.005):
    """Kafka delivers at least once, so the same event can show up twice."""
    n = int(len(events) * share)
    picks = rng.choice(len(events), size=n, replace=False)
    return events + [events[i] for i in picks]


def split_by_day(events, cutoff: date):
    """Events up to the cutoff day are history; later ones wait in the pending queue."""
    past = [e for e in events if e["event_ts"][:10] <= cutoff.isoformat()]
    future = [e for e in events if e["event_ts"][:10] > cutoff.isoformat()]
    return past, future


def to_frame(events) -> pd.DataFrame:
    return pd.DataFrame(events)

