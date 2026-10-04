import plotly.graph_objects as go
import streamlit as st
from data import municipalities, table

st.title("Risk by region")
st.caption("Claims per 1,000 policies for each municipality, all years together.")
risk = table("mart_region_risk")
min_policies = st.slider("Only municipalities with at least this many policies", 10, 200, 50, step=10)
shown = risk[risk["policies"] >= min_policies]

fig = go.Figure(go.Choropleth(
    geojson=municipalities(),
    featureidkey="properties.statcode",
    locations=shown["gm_code"],
    z=shown["claims_per_1000_policies"],
    colorscale="Blues",
    marker_line_color="white",
    marker_line_width=0.5,
    customdata=shown[["municipality", "policies", "claims"]],
    hovertemplate="<b>%{customdata[0]}</b><br>%{z:.0f} claims per 1,000 policies"
                  "<br>%{customdata[1]} policies, %{customdata[2]} claims<extra></extra>",
))
fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator")
fig.update_layout(height=620, margin=dict(l=0, r=0, t=0, b=0))

left, right = st.columns([3, 2])
with left:
    st.plotly_chart(fig, width="stretch")
with right:
    by_urbanity = (shown.groupby("urbanity_level", as_index=False)[["policies", "claims"]].sum())
    by_urbanity["per_1000"] = (1000 * by_urbanity["claims"] / by_urbanity["policies"]).round(0)
    st.subheader("By urbanity (1 = most urban)")
    st.dataframe(by_urbanity, hide_index=True, width="stretch")