from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from commerce_platform.bronze import LOAD_ORDER, load_bronze
from commerce_platform.paths import PlatformPaths, get_paths
from commerce_platform.streaming import read_stream_bronze


def run_silver(profile: str = "ci", data_root: str | Path | None = None) -> dict[str, int]:
    paths = get_paths(data_root)
    load_bronze(profile, paths.data_root)
    bronze_root = _latest_zone_partition(paths, "bronze", profile)
    run_partition = bronze_root.name
    silver_root = paths.zone("silver") / f"profile={profile}" / run_partition
    silver_root.mkdir(parents=True, exist_ok=True)

    frames = {table: pd.read_parquet(bronze_root / table / "part-000.parquet") for table in LOAD_ORDER}
    web_events = frames["web_events"]
    stream_events = read_stream_bronze(profile, paths.data_root)
    if not stream_events.empty:
        for column in web_events.columns:
            if column not in stream_events.columns:
                stream_events[column] = None
        stream_events["ingest_profile"] = profile
        stream_events["ingest_run_date"] = "stream"
        web_events = pd.concat([web_events, stream_events[web_events.columns]], ignore_index=True)

    transformed = {
        "customers": _customers(frames["customers"]),
        "products": _products(frames["products"]),
        "warehouses": _warehouses(frames["warehouses"]),
        "inventory": _inventory(frames["inventory"]),
        "orders": _orders(frames["orders"]),
        "order_items": _order_items(frames["order_items"]),
        "payments": _payments(frames["payments"]),
        "shipments": _shipments(frames["shipments"]),
        "returns": _returns(frames["returns"]),
        "web_events": _web_events(web_events),
    }

    counts = {}
    for table, frame in transformed.items():
        table_dir = silver_root / table
        table_dir.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(table_dir / "part-000.parquet", index=False)
        counts[table] = len(frame)

    manifest = pd.DataFrame(
        [
            {
                "profile": profile,
                "run_partition": run_partition,
                "table_name": table,
                "silver_rows": row_count,
            }
            for table, row_count in counts.items()
        ]
    )
    manifest.to_csv(paths.exports / "silver_manifest.csv", index=False)
    manifest.to_parquet(paths.zone("observability") / "silver_manifest.parquet", index=False)
    return counts


def latest_silver_partition(paths: PlatformPaths, profile: str) -> Path:
    return _latest_zone_partition(paths, "silver", profile)


def _latest_zone_partition(paths: PlatformPaths, zone: str, profile: str) -> Path:
    base = paths.zone(zone) / f"profile={profile}"
    candidates = sorted(base.glob("run_date=*"))
    if not candidates and zone == "silver":
        run_silver(profile, paths.data_root)
        candidates = sorted(base.glob("run_date=*"))
    if not candidates:
        raise FileNotFoundError(f"No {zone} partition found under {base}")
    return candidates[-1]


def _customers(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("customer_id").copy()
    out["email_hash"] = out["email"].astype(str).map(_hash_value)
    out["signup_date"] = pd.to_datetime(out["signup_date"], errors="coerce").dt.date.astype(str)
    out = out.drop(columns=["email"])
    return out[
        [
            "customer_id",
            "email_hash",
            "region",
            "acquisition_channel",
            "signup_date",
            "loyalty_tier",
            "ingest_profile",
            "ingest_run_date",
        ]
    ]


def _products(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("product_id").copy()
    out["unit_cost"] = pd.to_numeric(out["unit_cost"], errors="coerce").round(2)
    out["unit_price"] = pd.to_numeric(out["unit_price"], errors="coerce").round(2)
    out["gross_margin_pct"] = ((out["unit_price"] - out["unit_cost"]) / out["unit_price"]).round(4)
    out["active"] = out["active"].astype(bool)
    return out


def _warehouses(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("warehouse_id").copy()
    out["capacity_units"] = pd.to_numeric(out["capacity_units"], errors="coerce").astype("int64")
    out["priority"] = pd.to_numeric(out["priority"], errors="coerce").astype("int64")
    return out


def _inventory(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates(["warehouse_id", "product_id", "snapshot_date"]).copy()
    out["on_hand_units"] = pd.to_numeric(out["on_hand_units"], errors="coerce").astype("int64")
    out["reorder_point"] = pd.to_numeric(out["reorder_point"], errors="coerce").astype("int64")
    out["inventory_risk"] = out["on_hand_units"] <= out["reorder_point"]
    return out


def _orders(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("order_id").copy()
    out["order_ts"] = pd.to_datetime(out["order_ts"], utc=True)
    out["order_date"] = out["order_ts"].dt.date.astype(str)
    out["order_month"] = out["order_ts"].dt.tz_localize(None).dt.to_period("M").astype(str)
    return out


def _order_items(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("order_item_id").copy()
    out["quantity"] = pd.to_numeric(out["quantity"], errors="coerce").astype("int64")
    out["unit_price"] = pd.to_numeric(out["unit_price"], errors="coerce").round(2)
    out["discount_pct"] = pd.to_numeric(out["discount_pct"], errors="coerce").fillna(0).round(4)
    out["gross_sales"] = (out["quantity"] * out["unit_price"]).round(2)
    out["net_sales"] = (out["gross_sales"] * (1 - out["discount_pct"])).round(2)
    return out


def _payments(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("payment_id").copy()
    out["payment_ts"] = pd.to_datetime(out["payment_ts"], utc=True)
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce").round(2)
    out["is_successful_payment"] = out["payment_status"].isin(["authorized", "captured"])
    return out


def _shipments(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("shipment_id").copy()
    for column in ["ship_ts", "promised_delivery_ts", "delivered_ts"]:
        out[column] = pd.to_datetime(out[column], utc=True)
    out["delivery_hours"] = ((out["delivered_ts"] - out["ship_ts"]).dt.total_seconds() / 3600).round(2)
    out["delivered_on_time"] = out["delivered_ts"] <= out["promised_delivery_ts"]
    out["shipping_cost"] = pd.to_numeric(out["shipping_cost"], errors="coerce").round(2)
    return out


def _returns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("return_id").copy()
    out["return_ts"] = pd.to_datetime(out["return_ts"], utc=True)
    out["refund_amount"] = pd.to_numeric(out["refund_amount"], errors="coerce").round(2)
    return out


def _web_events(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.drop_duplicates("event_id").copy()
    out["event_ts"] = pd.to_datetime(out["event_ts"], utc=True)
    out["event_date"] = out["event_ts"].dt.date.astype(str)
    out["event_month"] = out["event_ts"].dt.tz_localize(None).dt.to_period("M").astype(str)
    out["is_late_event"] = out["event_ts"] < pd.Timestamp("2025-01-01", tz="UTC")
    return out


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()
