from __future__ import annotations

from commerce_platform.generator import generate_batch
from commerce_platform.silver import run_silver
from commerce_platform.streaming import consume_stream_events, produce_stream_events


def test_streaming_consumer_uses_checkpoint(tmp_path):
    produce_stream_events("ci", tmp_path, event_count=12)

    first = consume_stream_events("ci", tmp_path, max_events=5)
    second = consume_stream_events("ci", tmp_path, max_events=5)
    third = consume_stream_events("ci", tmp_path, max_events=5)
    fourth = consume_stream_events("ci", tmp_path, max_events=5)

    assert first["events_consumed"] == 5
    assert second["events_consumed"] == 5
    assert third["events_consumed"] == 2
    assert fourth["events_consumed"] == 0


def test_stream_events_flow_into_silver_events(tmp_path):
    generate_batch("ci", tmp_path)
    produce_stream_events("ci", tmp_path, event_count=10)
    consume_stream_events("ci", tmp_path)

    counts = run_silver("ci", tmp_path)
    assert counts["web_events"] == 2510
    assert (tmp_path / "exports/streaming_freshness.csv").exists()
