from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from commerce_platform.dashboard_data import (
    DEFAULT_QUERY,
    ensure_dashboard_data,
    executive_kpis,
    load_export,
    run_dashboard_query,
)

st.set_page_config(page_title="E-Commerce Data Platform", page_icon="database", layout="wide")

st.title("E-Commerce Cloud Data Platform")
st.caption("Batch + streaming lakehouse, DuckDB marts, quality observability, and AWS-ready architecture.")

profile = st.sidebar.selectbox("Profile", ["ci", "demo", "full"], index=0)
with st.spinner("Preparing platform data if needed..."):
    ensure_dashboard_data(profile=profile)

kpis = executive_kpis()
cols = st.columns(5)
cols[0].metric("Revenue", f"EGP {kpis['revenue']:,.0f}")
cols[1].metric("Orders", f"{kpis['orders']:,.0f}")
cols[2].metric("Customers", f"{kpis['customers']:,.0f}")
cols[3].metric("On-time SLA", f"{kpis['on_time_rate']:.1%}")
cols[4].metric("Platform Score", f"{kpis['platform_score']:.1f}%")

tabs = st.tabs(["Revenue", "Funnel", "Inventory", "Quality", "SQL"])

with tabs[0]:
    revenue = load_export("mart_revenue_daily.csv")
    if not revenue.empty:
        daily = revenue.groupby("order_date", as_index=False)["revenue"].sum()
        st.plotly_chart(px.line(daily, x="order_date", y="revenue", title="Daily Revenue"), use_container_width=True)
        st.dataframe(revenue.sort_values("revenue", ascending=False).head(50), use_container_width=True)

with tabs[1]:
    funnel = load_export("mart_funnel_conversion.csv")
    if not funnel.empty:
        metrics = funnel[["product_views", "add_to_cart", "checkout_starts", "purchase_events"]].sum().reset_index()
        metrics.columns = ["stage", "events"]
        st.plotly_chart(px.bar(metrics, x="stage", y="events", title="Event Funnel"), use_container_width=True)
        st.dataframe(funnel.sort_values("sessions", ascending=False).head(50), use_container_width=True)

with tabs[2]:
    inventory = load_export("mart_inventory_risk.csv")
    if not inventory.empty:
        risk = inventory.groupby("risk_band", as_index=False).size()
        st.plotly_chart(px.bar(risk, x="risk_band", y="size", title="Inventory Risk Bands"), use_container_width=True)
        st.dataframe(
            inventory.sort_values(["inventory_risk", "on_hand_units"], ascending=[False, True]).head(75),
            use_container_width=True,
        )

with tabs[3]:
    scorecard = load_export("platform_scorecard.csv")
    checks = load_export("quality_checks.csv")
    contract_summary = load_export("contract_summary.csv")
    freshness = load_export("streaming_freshness.csv")
    st.subheader("Scorecard")
    st.dataframe(scorecard, use_container_width=True)
    st.subheader("Quality Checks")
    st.dataframe(checks, use_container_width=True)
    st.subheader("Contract Summary")
    st.dataframe(contract_summary, use_container_width=True)
    if not freshness.empty:
        st.subheader("Streaming Freshness")
        st.dataframe(freshness, use_container_width=True)

with tabs[4]:
    query = st.text_area("DuckDB SQL", value=DEFAULT_QUERY, height=180)
    if st.button("Run query"):
        try:
            result = run_dashboard_query(query)
            st.dataframe(result, use_container_width=True)
            st.download_button(
                "Download CSV",
                result.to_csv(index=False).encode("utf-8"),
                file_name="query_result.csv",
                mime="text/csv",
            )
        except Exception as exc:
            st.error(str(exc))

footer = pd.DataFrame(
    [
        {"layer": "bronze", "purpose": "raw batch and streaming landing"},
        {"layer": "silver", "purpose": "typed, deduped, PII-safe business entities"},
        {"layer": "gold", "purpose": "DuckDB marts for BI and recruiter-visible KPIs"},
    ]
)
st.sidebar.dataframe(footer, hide_index=True)
