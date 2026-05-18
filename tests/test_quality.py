from __future__ import annotations

import pandas as pd

from commerce_platform.generator import generate_batch
from commerce_platform.quality import run_quality


def test_run_quality_exports_scorecard_and_report(tmp_path):
    generate_batch("ci", tmp_path)
    result = run_quality("ci", tmp_path)

    assert result["score"] > 80
    assert (tmp_path / "exports/data_quality_report.md").exists()
    scorecard = pd.read_csv(tmp_path / "exports/platform_scorecard.csv")
    assert scorecard.iloc[0]["checks_failed"] == 0
