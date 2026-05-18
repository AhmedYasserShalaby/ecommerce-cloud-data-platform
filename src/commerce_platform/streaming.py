from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pandas as pd

from commerce_platform.generator import CHANNELS, EVENT_TYPES
from commerce_platform.paths import get_paths
from commerce_platform.profiles import get_profile


STREAM_TOPIC_FILE = "commerce.events.jsonl"
CHECKPOINT_FILE = "commerce.events.checkpoint.json"


def produce_stream_events(
    profile: str = "ci",
    data_root: str | Path | None = None,
    event_count: int = 250,
) -> dict[str, int | str]:
    paths = get_paths(data_root)
    paths.stream.mkdir(parents=True, exist_ok=True)
    profile_config = get_profile(profile)
    rng = random.Random(profile_config.seed + 777)
    topic_path = paths.stream / STREAM_TOPIC_FILE
    now = datetime(2026, 5, 18, tzinfo=UTC)

    with topic_path.open("a", encoding="utf-8") as handle:
        for index in range(event_count):
            event = {
                "event_id": str(uuid5(NAMESPACE_URL, f"{profile}:stream:{topic_path.stat().st_size}:{index}")),
                "customer_id": f"cust_{rng.randint(1, profile_config.customers):08d}",
                "session_id": f"live_sess_{rng.randint(1, max(1, event_count // 5)):08d}",
                "event_ts": (now + timedelta(seconds=index * 3)).isoformat(),
                "event_type": rng.choices(EVENT_TYPES, weights=[38, 30, 14, 8, 4, 6])[0],
                "product_id": f"prod_{rng.randint(1, profile_config.products):08d}",
                "device": rng.choice(["ios", "android", "web", "mobile_web"]),
                "campaign": rng.choice(CHANNELS),
                "event_source": "stream",
            }
            handle.write(json.dumps(event) + "\n")
    return {"topic_path": str(topic_path), "events_produced": event_count}


def consume_stream_events(
    profile: str = "ci",
    data_root: str | Path | None = None,
    max_events: int | None = None,
) -> dict[str, int | str]:
    paths = get_paths(data_root)
    topic_path = paths.stream / STREAM_TOPIC_FILE
    checkpoint_path = paths.stream / CHECKPOINT_FILE
    if not topic_path.exists():
        return {"events_consumed": 0, "checkpoint": "0", "output_path": ""}

    checkpoint = _read_checkpoint(checkpoint_path)
    lines = topic_path.read_text(encoding="utf-8").splitlines()
    new_lines = lines[checkpoint:]
    if max_events is not None:
        new_lines = new_lines[:max_events]
    if not new_lines:
        return {"events_consumed": 0, "checkpoint": str(checkpoint), "output_path": ""}

    events = [json.loads(line) for line in new_lines if line.strip()]
    new_checkpoint = checkpoint + len(events)
    stream_root = paths.lake / "bronze_stream" / f"profile={profile}" / "web_events"
    stream_root.mkdir(parents=True, exist_ok=True)
    output_path = stream_root / f"micro_batch_{new_checkpoint:08d}.parquet"
    frame = pd.DataFrame(events)
    frame["stream_offset_start"] = checkpoint
    frame["stream_offset_end"] = new_checkpoint
    frame.to_parquet(output_path, index=False)
    checkpoint_path.write_text(json.dumps({"offset": new_checkpoint}, indent=2), encoding="utf-8")
    _write_stream_freshness(paths.exports / "streaming_freshness.csv", profile, frame, new_checkpoint)
    return {"events_consumed": len(frame), "checkpoint": str(new_checkpoint), "output_path": str(output_path)}


def read_stream_bronze(profile: str, data_root: str | Path | None = None) -> pd.DataFrame:
    paths = get_paths(data_root)
    stream_root = paths.lake / "bronze_stream" / f"profile={profile}" / "web_events"
    files = sorted(stream_root.glob("micro_batch_*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(path) for path in files], ignore_index=True)


def _read_checkpoint(path: Path) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    return int(payload.get("offset", 0))


def _write_stream_freshness(path: Path, profile: str, frame: pd.DataFrame, checkpoint: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    freshness = pd.DataFrame(
        [
            {
                "profile": profile,
                "topic": "commerce.events",
                "latest_event_ts": pd.to_datetime(frame["event_ts"], utc=True).max().isoformat(),
                "events_consumed": len(frame),
                "checkpoint": checkpoint,
            }
        ]
    )
    freshness.to_csv(path, index=False)
