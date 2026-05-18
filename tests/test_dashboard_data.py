from __future__ import annotations

from commerce_platform.dashboard_data import executive_kpis, run_dashboard_query
from commerce_platform.generator import generate_batch
from commerce_platform.quality import run_quality


def test_dashboard_query_reads_warehouse(tmp_path):
    generate_batch("ci", tmp_path)
    run_quality("ci", tmp_path)

    result = run_dashboard_query("select count(*) as rows from mart_revenue_daily", tmp_path)
    assert result.iloc[0]["rows"] > 0


def test_executive_kpis_are_nonzero(tmp_path):
    generate_batch("ci", tmp_path)
    run_quality("ci", tmp_path)

    kpis = executive_kpis(tmp_path)
    assert kpis["revenue"] > 0
    assert kpis["platform_score"] == 100
