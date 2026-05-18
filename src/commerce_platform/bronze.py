from __future__ import annotations

from pathlib import Path

import pandas as pd

from commerce_platform.contracts import load_contracts, read_source, validate_table
from commerce_platform.generator import generate_batch
from commerce_platform.paths import PlatformPaths, get_paths

LOAD_ORDER = [
    "customers",
    "products",
    "warehouses",
    "inventory",
    "orders",
    "order_items",
    "payments",
    "shipments",
    "returns",
    "web_events",
]


def latest_batch_dir(paths: PlatformPaths, profile: str) -> Path:
    base = paths.raw / "batch" / f"profile={profile}"
    candidates = sorted(base.glob("run_date=*"))
    if candidates:
        return candidates[-1]
    generate_batch(profile, paths.data_root)
    candidates = sorted(base.glob("run_date=*"))
    if not candidates:
        raise FileNotFoundError(f"No raw batch found under {base}")
    return candidates[-1]


def load_bronze(profile: str = "ci", data_root: str | Path | None = None) -> dict[str, int]:
    paths = get_paths(data_root)
    batch_dir = latest_batch_dir(paths, profile)
    contracts = load_contracts()

    source_frames: dict[str, pd.DataFrame] = {}
    for table in LOAD_ORDER:
        source_path = batch_dir / f"{table}.csv"
        if table == "web_events":
            source_path = batch_dir / "web_events.jsonl"
        source_frames[table] = read_source(source_path)

    clean_counts: dict[str, int] = {}
    rejected_frames: list[pd.DataFrame] = []
    issue_frames: list[pd.DataFrame] = []
    reference_frames: dict[str, pd.DataFrame] = {}

    bronze_root = paths.zone("bronze") / f"profile={profile}" / batch_dir.name
    bronze_root.mkdir(parents=True, exist_ok=True)

    for table in LOAD_ORDER:
        result = validate_table(table, source_frames[table], contracts, reference_frames)
        table_dir = bronze_root / table
        table_dir.mkdir(parents=True, exist_ok=True)
        output = result.clean.copy()
        output["ingest_profile"] = profile
        output["ingest_run_date"] = batch_dir.name.replace("run_date=", "")
        output.to_parquet(table_dir / "part-000.parquet", index=False)
        clean_counts[table] = len(result.clean)
        reference_frames[table] = result.clean
        if not result.rejected.empty:
            rejected_frames.append(result.rejected)
        if not result.issues.empty:
            issue_frames.append(result.issues)

    observability_dir = paths.zone("observability")
    observability_dir.mkdir(parents=True, exist_ok=True)
    issues = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    rejected = pd.concat(rejected_frames, ignore_index=True, sort=False) if rejected_frames else pd.DataFrame()
    summary = _contract_summary(profile, batch_dir.name, source_frames, clean_counts, issues)

    paths.exports.mkdir(parents=True, exist_ok=True)
    issues.to_csv(paths.exports / "contract_issues.csv", index=False)
    rejected.to_csv(paths.exports / "rejected_rows.csv", index=False)
    summary.to_csv(paths.exports / "contract_summary.csv", index=False)
    summary.to_parquet(observability_dir / "contract_summary.parquet", index=False)
    return clean_counts


def _contract_summary(
    profile: str,
    run_partition: str,
    source_frames: dict[str, pd.DataFrame],
    clean_counts: dict[str, int],
    issues: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    issues_by_table = issues.groupby("table_name").size().to_dict() if not issues.empty else {}
    for table, source in source_frames.items():
        raw_rows = len(source)
        clean_rows = clean_counts.get(table, 0)
        rejected_rows = raw_rows - clean_rows
        rows.append(
            {
                "profile": profile,
                "run_partition": run_partition,
                "table_name": table,
                "raw_rows": raw_rows,
                "clean_rows": clean_rows,
                "rejected_rows": rejected_rows,
                "validation_issues": int(issues_by_table.get(table, 0)),
                "quality_score": round((clean_rows / raw_rows) * 100, 2) if raw_rows else 100.0,
            }
        )
    return pd.DataFrame(rows)
