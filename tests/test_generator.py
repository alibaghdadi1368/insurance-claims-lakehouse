"""Checks on the synthetic data, run with `pytest -q` from the repo root.

They use small in-memory samples so the whole file runs in a few seconds.
"""

from datetime import date

import numpy as np
import pandas as pd
import pytest
from faker import Faker

from generator import claims, config, people, policies
from generator.run import claim_context


@pytest.fixture(scope="module")
def book():
    rng = np.random.default_rng(1)
    fake = Faker("nl_NL")
    fake.seed_instance(1)
    pcs = people.load_postcodes()
    cust = people.make_customers(300, 1, date(2020, 1, 1), date(2026, 9, 30), rng, fake, pcs)
    veh = people.make_vehicles(cust, 1, rng)
    pols = policies.make_policies(veh, cust, pcs, 1, rng, latest_start=date(2026, 9, 30))
    ctx = claim_context(pols, cust, veh, pcs)
    events, _ = claims.claims_for_period(pols, ctx, date(2024, 1, 1), date(2026, 9, 30), rng, 1)
    return cust, veh, pols, events


def test_postcodes_look_dutch(book):
    cust = book[0]
    assert cust["postcode"].str.fullmatch(r"\d{4} [A-Z]{2}").all()
    assert not cust["postcode"].str[-2:].isin(["SA", "SD", "SS"]).any()


def test_every_vehicle_and_policy_has_an_owner(book):
    cust, veh, pols, _ = book
    assert set(veh["customer_id"]) <= set(cust["customer_id"])
    assert set(pols["vehicle_id"]) == set(veh["vehicle_id"])


def test_policy_dates_make_sense(book):
    pols = book[2]
    ended = pols.dropna(subset=["end_date"])
    assert (ended["end_date"] >= ended["start_date"]).all()
    assert set(pols["status"]) <= {"active", "cancelled"}


def test_claim_events_follow_the_lifecycle(book):
    events = pd.DataFrame(book[3])
    order = {"CLAIM_REPORTED": 0, "CLAIM_ASSESSED": 1, "CLAIM_APPROVED": 2,
             "CLAIM_REJECTED": 2, "CLAIM_PAID": 3}
    events["step"] = events["event_type"].map(order)
    for _, claim in events.groupby("claim_id"):
        assert claim.sort_values("event_ts")["step"].is_monotonic_increasing
        assert claim["event_type"].iloc[0] == "CLAIM_REPORTED"


def test_payout_never_exceeds_claim(book):
    events = pd.DataFrame(book[3])
    claimed = events[events.event_type == "CLAIM_REPORTED"].set_index("claim_id")["payload"].map(
        lambda p: p["claimed_amount"])
    paid = events[events.event_type == "CLAIM_PAID"].set_index("claim_id")["payload"].map(
        lambda p: p["paid_amount"])
    assert (paid <= claimed.loc[paid.index]).all()
    assert (paid > 0).all()


def test_only_covered_claim_types(book):
    pols = book[2].set_index("policy_id")
    for e in book[3]:
        if e["event_type"] == "CLAIM_REPORTED":
            product = pols.loc[e["policy_id"], "product_code"]
            assert product in config.CLAIM_TYPES[e["payload"]["claim_type"]]["products"]


def test_same_seed_same_data():
    def run():
        rng = np.random.default_rng(7)
        fake = Faker("nl_NL")
        fake.seed_instance(7)
        return people.make_customers(50, 1, date(2020, 1, 1), date(2021, 1, 1), rng, fake, people.load_postcodes())

    pd.testing.assert_frame_equal(run(), run())