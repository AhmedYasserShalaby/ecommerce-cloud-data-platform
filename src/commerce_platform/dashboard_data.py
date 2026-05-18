from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from commerce_platform.paths import get_paths
from commerce_platform.quality import run_quality

DEFAULT_QUERY = """
select order_date, region, revenue, gross_margin_pct
from mart_revenue_daily
order by order_date desc, revenue desc
limit 25
""".strip()


def ensure_dashboard_data(data_root: str | Path | None = None, profile: str = "ci") -> Path:
    paths = get_paths(data_root)
    warehouse = paths.warehouse / "commerce.duckdb"
    if not warehouse.exists():
        run_quality(profile, paths.data_root)
    return warehouse


def load_export(name: str, data_root: str | Path | None = None) -> pd.DataFrame:
    paths = get_paths(data_root)
    path = paths.exports / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def run_dashboard_query(query: str = DEFAULT_QUERY, data_root: str | Path | None = None) -> pd.DataFrame:
    warehouse = ensure_dashboard_data(data_root)
    connection = duckdb.connect(str(warehouse), read_only=True)
    try:
        return connection.sql(query).df()
    finally:
        connection.close()


def executive_kpis(data_root: str | Path | None = None) -> dict[str, float]:
    revenue = load_export("mart_revenue_daily.csv", data_root)
    customers = load_export("mart_customer_ltv.csv", data_root)
    fulfillment = load_export("mart_fulfillment_sla.csv", data_root)
    scorecard = load_export("platform_scorecard.csv", data_root)
    return {
        "revenue": float(revenue["revenue"].sum()) if not revenue.empty else 0.0,
        "orders": float(revenue["total_orders"].sum()) if not revenue.empty else 0.0,
        "customers": float(len(customers)) if not customers.empty else 0.0,
        "on_time_rate": float(fulfillment["on_time_rate"].mean()) if not fulfillment.empty else 0.0,
        "platform_score": float(scorecard.iloc[0]["platform_score"]) if not scorecard.empty else 0.0,
    }
