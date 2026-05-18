from __future__ import annotations

import json

from commerce_platform.generator import generate_batch


def test_generate_batch_is_deterministic(tmp_path):
    first = generate_batch("ci", tmp_path / "first")
    second = generate_batch("ci", tmp_path / "second")

    assert first["tables"] == second["tables"]
    assert first["web_events"] == second["web_events"] == 2500

    first_customers = (tmp_path / "first/raw/batch/profile=ci/run_date=2026-05-18/customers.csv").read_text()
    second_customers = (tmp_path / "second/raw/batch/profile=ci/run_date=2026-05-18/customers.csv").read_text()
    assert first_customers == second_customers


def test_generate_batch_writes_manifest_and_dirty_records(tmp_path):
    manifest = generate_batch("ci", tmp_path)
    manifest_path = tmp_path / "raw/batch/profile=ci/run_date=2026-05-18/manifest.json"

    saved_manifest = json.loads(manifest_path.read_text())
    assert saved_manifest["dirty_records_seeded"]["duplicate_order_id"] == 1
    assert manifest["tables"]["orders"] == 601
    assert (tmp_path / "raw/batch/profile=ci/run_date=2026-05-18/web_events.jsonl").exists()
