"""
Polder Verzekeringen claims dashboard.

    streamlit run dashboard/app.py
"""
import streamlit as st
from data import live_mode

st.set_page_config(page_title="Polder Verzekeringen", page_icon="🚗", layout="wide")
st.sidebar.markdown("### Polder Verzekeringen")
st.sidebar.caption("A made-up Dutch car insurer. All data is synthetic.")
st.sidebar.caption("Source: " + ("Snowflake GOLD (live)" if live_mode() else "demo snapshot"))

pages = [
    st.Page("pages/overview.py", title="Overview", icon=":material/dashboard:", default=True),
    st.Page("pages/claims.py", title="Claim handling", icon=":material/schedule:"),
    st.Page("pages/fraud.py", title="Fraud signals", icon=":material/flag:"),
    st.Page("pages/regions.py", title="Risk by region", icon=":material/map:"),
]
st.navigation(pages).run()