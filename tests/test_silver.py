from __future__ import annotations

import pandas as pd

from commerce_platform.generator import generate_batch
from commerce_platform.silver import run_silver


def test_run_silver_hashes_pii_and_adds_order_metrics(tmp_path):
    generate_batch("ci", tmp_path)
    counts = run_silver("ci", tmp_path)

    assert counts["customers"] == 40
    customers = pd.read_parquet(tmp_path / "lake/silver/profile=ci/run_date=2026-05-18/customers/part-000.parquet")
    assert "email" not in customers.columns
    assert customers["email_hash"].str.len().eq(64).all()

    order_items = pd.read_parquet(tmp_path / "lake/silver/profile=ci/run_date=2026-05-18/order_items/part-000.parquet")
    assert {"gross_sales", "net_sales"}.issubset(order_items.columns)
    assert order_items["net_sales"].min() > 0


def test_run_silver_flags_late_events(tmp_path):
    generate_batch("ci", tmp_path)
    run_silver("ci", tmp_path)

    events = pd.read_parquet(tmp_path / "lake/silver/profile=ci/run_date=2026-05-18/web_events/part-000.parquet")
    assert events["is_late_event"].sum() >= 1
