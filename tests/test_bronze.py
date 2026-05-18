from __future__ import annotations

import pandas as pd

from commerce_platform.bronze import load_bronze
from commerce_platform.generator import generate_batch


def test_load_bronze_writes_clean_parquet_and_rejections(tmp_path):
    generate_batch("ci", tmp_path)
    counts = load_bronze("ci", tmp_path)

    assert counts["customers"] == 40
    assert counts["orders"] == 599
    assert (tmp_path / "lake/bronze/profile=ci/run_date=2026-05-18/orders/part-000.parquet").exists()

    issues = pd.read_csv(tmp_path / "exports/contract_issues.csv")
    assert "duplicate_key" in set(issues["issue_type"])
    assert "missing_fk:customers.customer_id" in set(issues["issue_type"])


def test_contract_summary_tracks_quality_score(tmp_path):
    generate_batch("ci", tmp_path)
    load_bronze("ci", tmp_path)

    summary = pd.read_csv(tmp_path / "exports/contract_summary.csv")
    orders = summary.loc[summary["table_name"] == "orders"].iloc[0]
    assert orders["raw_rows"] == 601
    assert orders["clean_rows"] == 599
    assert orders["quality_score"] < 100
