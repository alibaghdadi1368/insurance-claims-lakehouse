import streamlit as st
from data import table

st.title("Fraud signals")
st.caption("Claims with two or more warning signs. A list to review, not a verdict.")
flags = table("mart_fraud_signals")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Flagged claims", f"{len(flags):,}")
c2.metric("Already paid", f"€{flags['paid_amount'].fillna(0).sum():,.0f}")
c3.metric("Rejected", f"{(flags['claim_status'] == 'rejected').sum():,}")
# not decided yet, so a payment can still be stopped
c4.metric("Still open", f"{flags['claim_status'].isin(['reported', 'assessed', 'approved']).sum():,}",
          help="Reported, assessed or approved but not paid yet: these can still be stopped.")

min_score = st.slider("Minimum number of warning signs", 2, 4, 2)
status = st.multiselect("Status", sorted(flags["claim_status"].unique()), default=sorted(flags["claim_status"].unique()))
view = flags[(flags["risk_score"] >= min_score) & flags["claim_status"].isin(status)]

st.dataframe(
    view.sort_values(["risk_score", "claimed_amount"], ascending=False)[
        ["claim_id", "claim_type", "claim_status", "reported_date", "claimed_amount",
         "catalog_value_eur", "days_after_policy_start", "risk_score", "reasons"]
    ],
    hide_index=True,
    width="stretch",
    column_config={
        "reported_date": st.column_config.DateColumn("Reported"),
        "claimed_amount": st.column_config.NumberColumn("Claimed (€)", format="%.0f"),
        "catalog_value_eur": st.column_config.NumberColumn("Car value (€)", format="%.0f"),
        "days_after_policy_start": st.column_config.NumberColumn("Days after start"),
        "risk_score": st.column_config.ProgressColumn("Signs", min_value=0, max_value=4, format="%d"),
    },
)