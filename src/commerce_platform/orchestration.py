from __future__ import annotations

from pathlib import Path

from commerce_platform.generator import generate_batch
from commerce_platform.gold import run_gold
from commerce_platform.paths import get_paths
from commerce_platform.quality import run_quality
from commerce_platform.streaming import consume_stream_events, produce_stream_events


def run_all(profile: str = "ci", data_root: str | Path | None = None) -> dict[str, object]:
    batch_manifest = generate_batch(profile, data_root)
    stream_produce = produce_stream_events(profile, data_root, event_count=_stream_count(profile))
    stream_consume = consume_stream_events(profile, data_root)
    gold_counts = run_gold(profile, data_root)
    return {
        "batch_manifest": batch_manifest,
        "stream_produce": stream_produce,
        "stream_consume": stream_consume,
        "gold_counts": gold_counts,
    }


def smoke(profile: str = "ci", data_root: str | Path | None = None) -> dict[str, object]:
    paths = get_paths(data_root)
    quality_result = run_quality(profile, paths.data_root)
    required = [
        paths.exports / "mart_revenue_daily.csv",
        paths.exports / "mart_customer_ltv.csv",
        paths.exports / "mart_funnel_conversion.csv",
        paths.exports / "platform_scorecard.csv",
        paths.warehouse / "commerce.duckdb",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Smoke failed; missing outputs: {missing}")
    return {"quality": quality_result, "checked_outputs": len(required)}


def _stream_count(profile: str) -> int:
    return {"ci": 250, "demo": 5_000, "full": 100_000}[profile]
