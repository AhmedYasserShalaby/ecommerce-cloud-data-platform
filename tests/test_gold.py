from __future__ import annotations

import duckdb
import pandas as pd

from commerce_platform.generator import generate_batch
from commerce_platform.gold import run_gold


def test_run_gold_builds_required_marts(tmp_path):
    generate_batch("ci", tmp_path)
    counts = run_gold("ci", tmp_path)

    assert counts["mart_revenue_daily"] > 0
    assert counts["mart_customer_ltv"] == 40
    assert (tmp_path / "warehouse/commerce.duckdb").exists()
    assert (tmp_path / "exports/mart_revenue_daily.csv").exists()


def test_revenue_mart_matches_duckdb_export(tmp_path):
    generate_batch("ci", tmp_path)
    run_gold("ci", tmp_path)

    exported = pd.read_csv(tmp_path / "exports/mart_revenue_daily.csv")
    connection = duckdb.connect(str(tmp_path / "warehouse/commerce.duckdb"))
    try:
        warehouse_revenue = connection.sql("select round(sum(revenue), 2) from mart_revenue_daily").fetchone()[0]
    finally:
        connection.close()
    assert round(exported["revenue"].sum(), 2) == warehouse_revenue
