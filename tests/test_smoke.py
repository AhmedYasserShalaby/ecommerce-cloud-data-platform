from __future__ import annotations

from commerce_platform.orchestration import smoke


def test_smoke_builds_required_outputs(tmp_path):
    result = smoke("ci", tmp_path)
    assert result["checked_outputs"] == 5
    assert (tmp_path / "warehouse/commerce.duckdb").exists()
