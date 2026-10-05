import plotly.express as px
import streamlit as st
from data import table

st.title("Overview")
st.caption("Premium, claims and loss ratio. Loss ratio = claims paid / premium due.")

lr = table("mart_loss_ratio_monthly")
products = st.multiselect("Products", sorted(lr["product_code"].unique()), default=sorted(lr["product_code"].unique()))
lr = lr[lr["product_code"].isin(products)]
premium = lr["premium_eur"].sum()
paid = lr["claims_paid_eur"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Premium due", f"€{premium / 1e6:,.2f}M")
c1.metric("Claims paid", f"€{paid / 1e6:,.2f}M")
c3.metric("Loss ratio", f"{paid / premium:.0%}" if premium else "-")
c4.metric("Claims reported", f"{lr['claims_reported'].sum():,}")

monthly = lr.groupby("month", as_index=False)[["premium_eur", "claims_paid_eur"]].sum()
monthly["loss_ratio"] = monthly["claims_paid_eur"] / monthly["premium_eur"]

left, right = st.columns(2)
with left:
    st.subheader("Loss ratio per month")
    fig = px.line(monthly, x="month", y="loss_ratio", markers=True)
    fig.add_hline(y=0.7, line_dash="dot", annotation_text="70% target")
    fig.update_layout(yaxis_tickformat=".0%", yaxis_title=None, xaxis_title=None, height=360)
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Loss ratio per product")
    by_product = lr.groupby("product_code", as_index=False)[["premium_eur", "claims_paid_eur"]].sum()
    by_product["loss_ratio"] = by_product["claims_paid_eur"] / by_product["premium_eur"]
    fig = px.bar(by_product, x="product_code", y="loss_ratio", text_auto=".0%")
    fig.update_layout(yaxis_tickformat=".0%", yaxis_title=None, xaxis_title=None, height=360)
    st.plotly_chart(fig, width="stretch")