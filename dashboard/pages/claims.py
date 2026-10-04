import plotly.express as px
import streamlit as st
from data import table

st.title("Claim handling")
st.caption("Service levels: a decision within 14 days and payment within 30 days of the report.")
claims = table("fct_claims")
sla = table("mart_claims_sla")
paid = claims[claims["paid_date"].notna()]

c1, c2, c3 = st.columns(3)
c1.metric("Open claims", f"{claims['claim_status'].isin(['reported', 'assessed', 'approved']).sum():,}")
c2.metric("Median days to payment", f"{paid['days_to_payment'].median():.0f}")
c3.metric("Paid within 30 days", f"{(paid['days_to_payment'] <= 30).mean():.0%}")

left, right = st.columns(2)
with left:
    st.subheader("Days from report to payment")
    fig = px.histogram(paid, x="days_to_payment", nbins=40)
    fig.add_vline(x=30, line_dash="dot", annotation_text="SLA")
    fig.update_layout(xaxis_title="days", yaxis_title="claims", height=360)
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Median days to payment by claim type")
    by_type = paid.groupby("claim_type", as_index=False)["days_to_payment"].median().sort_values("days_to_payment")
    fig = px.bar(by_type, x="days_to_payment", y="claim_type", orientation="h", text_auto=".0f")
    fig.update_layout(xaxis_title="days", yaxis_title=None, height=360)
    st.plotly_chart(fig, width="stretch")

st.subheader("Monthly service level")
monthly = sla.groupby("month", as_index=False).agg(claims=("claims", "sum"), paid_30d=("pct_paid_within_30d", "mean"))
fig = px.line(monthly, x="month", y="paid_30d", markers=True)
fig.update_layout(yaxis_tickformat=".0%", yaxis_title="paid within 30 days", xaxis_title=None, height=360)
st.plotly_chart(fig, width="stretch")