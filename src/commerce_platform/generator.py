from __future__ import annotations

import json
import random
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pandas as pd

from commerce_platform.paths import get_paths
from commerce_platform.profiles import DataProfile, get_profile

CATEGORIES = ["electronics", "home", "fashion", "beauty", "sports", "grocery", "books", "toys"]
REGIONS = ["Cairo", "Giza", "Alexandria", "Delta", "Upper Egypt", "Gulf"]
CHANNELS = ["organic", "paid_search", "social", "email", "partner", "direct"]
ORDER_STATUSES = ["created", "paid", "packed", "shipped", "delivered", "cancelled", "returned"]
EVENT_TYPES = ["page_view", "product_view", "add_to_cart", "checkout_start", "purchase", "search"]


def _id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:08d}"


def _stable_event_id(session_id: str, index: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"{session_id}:{index}"))


def _rand_date(rng: random.Random, start: datetime, days: int) -> datetime:
    return start + timedelta(minutes=rng.randint(0, days * 24 * 60))


def generate_batch(profile_name: str = "ci", data_root: str | Path | None = None) -> dict[str, object]:
    profile = get_profile(profile_name)
    paths = get_paths(data_root)
    run_date = "2026-05-18"
    batch_dir = paths.raw / "batch" / f"profile={profile.name}" / f"run_date={run_date}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(profile.seed)
    base_date = datetime(2025, 1, 1, tzinfo=UTC)

    customers = _generate_customers(profile, rng, base_date)
    products = _generate_products(profile, rng)
    warehouses = _generate_warehouses(profile, rng)
    inventory = _generate_inventory(profile, rng, products, warehouses, run_date)
    orders = _generate_orders(profile, rng, customers, base_date)
    order_items = _generate_order_items(profile, rng, orders, products, warehouses)
    payments = _generate_payments(rng, orders, order_items)
    shipments = _generate_shipments(rng, orders, warehouses)
    returns = _generate_returns(rng, order_items, orders)

    tables = {
        "customers": customers,
        "products": products,
        "warehouses": warehouses,
        "inventory": inventory,
        "orders": orders,
        "order_items": order_items,
        "payments": payments,
        "shipments": shipments,
        "returns": returns,
    }
    dirty_counts = _inject_dirty_records(tables, profile)

    for table_name, frame in tables.items():
        frame.to_csv(batch_dir / f"{table_name}.csv", index=False)

    event_path = batch_dir / "web_events.jsonl"
    web_event_count = _write_web_events(profile, rng, customers, products, event_path, base_date)
    manifest = {
        "profile": asdict(profile),
        "run_date": run_date,
        "batch_dir": str(batch_dir),
        "tables": {name: len(frame) for name, frame in tables.items()},
        "web_events": web_event_count,
        "dirty_records_seeded": dirty_counts,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    (batch_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _generate_customers(profile: DataProfile, rng: random.Random, base_date: datetime) -> pd.DataFrame:
    rows = []
    tiers = ["standard", "silver", "gold", "platinum"]
    for i in range(1, profile.customers + 1):
        region = rng.choice(REGIONS)
        rows.append(
            {
                "customer_id": _id("cust", i),
                "email": f"customer{i}@example.com",
                "region": region,
                "acquisition_channel": rng.choice(CHANNELS),
                "signup_date": _rand_date(rng, base_date - timedelta(days=365), 365).date().isoformat(),
                "loyalty_tier": rng.choices(tiers, weights=[60, 25, 12, 3])[0],
            }
        )
    return pd.DataFrame(rows)


def _generate_products(profile: DataProfile, rng: random.Random) -> pd.DataFrame:
    rows = []
    for i in range(1, profile.products + 1):
        category = rng.choice(CATEGORIES)
        cost = round(rng.uniform(25, 2_500), 2)
        margin = rng.uniform(1.15, 1.9)
        rows.append(
            {
                "product_id": _id("prod", i),
                "sku": f"{category[:3].upper()}-{i:06d}",
                "category": category,
                "brand": f"Brand {rng.randint(1, 40)}",
                "unit_cost": cost,
                "unit_price": round(cost * margin, 2),
                "active": rng.random() > 0.04,
            }
        )
    return pd.DataFrame(rows)


def _generate_warehouses(profile: DataProfile, rng: random.Random) -> pd.DataFrame:
    rows = []
    for i in range(1, profile.warehouses + 1):
        rows.append(
            {
                "warehouse_id": _id("wh", i),
                "region": REGIONS[(i - 1) % len(REGIONS)],
                "capacity_units": rng.randint(25_000, 180_000),
                "priority": rng.randint(1, 3),
            }
        )
    return pd.DataFrame(rows)


def _generate_inventory(
    profile: DataProfile, rng: random.Random, products: pd.DataFrame, warehouses: pd.DataFrame, run_date: str
) -> pd.DataFrame:
    rows = []
    sampled_products = products["product_id"].tolist()
    for warehouse_id in warehouses["warehouse_id"]:
        for product_id in sampled_products:
            reorder_point = rng.randint(25, 250)
            rows.append(
                {
                    "warehouse_id": warehouse_id,
                    "product_id": product_id,
                    "snapshot_date": run_date,
                    "on_hand_units": rng.randint(0, 1_500),
                    "reorder_point": reorder_point,
                }
            )
    return pd.DataFrame(rows)


def _generate_orders(
    profile: DataProfile, rng: random.Random, customers: pd.DataFrame, base_date: datetime
) -> pd.DataFrame:
    customer_ids = customers["customer_id"].tolist()
    rows = []
    for i in range(1, profile.orders + 1):
        created_at = _rand_date(rng, base_date, 500)
        rows.append(
            {
                "order_id": _id("ord", i),
                "customer_id": rng.choice(customer_ids),
                "order_ts": created_at.isoformat(),
                "status": rng.choices(ORDER_STATUSES, weights=[3, 8, 7, 15, 55, 7, 5])[0],
                "region": rng.choice(REGIONS),
                "currency": "EGP",
            }
        )
    return pd.DataFrame(rows)


def _generate_order_items(
    profile: DataProfile,
    rng: random.Random,
    orders: pd.DataFrame,
    products: pd.DataFrame,
    warehouses: pd.DataFrame,
) -> pd.DataFrame:
    product_rows = products.set_index("product_id").to_dict("index")
    product_ids = list(product_rows)
    warehouse_ids = warehouses["warehouse_id"].tolist()
    rows = []
    item_id = 1
    for order_id in orders["order_id"]:
        for _ in range(rng.choices([1, 2, 3, 4], weights=[55, 28, 12, 5])[0]):
            product_id = rng.choice(product_ids)
            product = product_rows[product_id]
            rows.append(
                {
                    "order_item_id": _id("item", item_id),
                    "order_id": order_id,
                    "product_id": product_id,
                    "warehouse_id": rng.choice(warehouse_ids),
                    "quantity": rng.choices([1, 2, 3, 4, 5], weights=[62, 23, 9, 4, 2])[0],
                    "unit_price": product["unit_price"],
                    "discount_pct": round(rng.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2]), 2),
                }
            )
            item_id += 1
    return pd.DataFrame(rows)


def _generate_payments(rng: random.Random, orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    order_totals = (
        order_items.assign(net=lambda df: df["quantity"] * df["unit_price"] * (1 - df["discount_pct"]))
        .groupby("order_id", as_index=False)["net"]
        .sum()
    )
    order_ts = orders.set_index("order_id")["order_ts"].to_dict()
    rows = []
    for index, row in enumerate(order_totals.itertuples(index=False), start=1):
        paid_at = datetime.fromisoformat(order_ts[row.order_id]) + timedelta(minutes=rng.randint(1, 180))
        rows.append(
            {
                "payment_id": _id("pay", index),
                "order_id": row.order_id,
                "payment_ts": paid_at.isoformat(),
                "payment_method": rng.choice(["card", "wallet", "cash_on_delivery", "bank_transfer"]),
                "payment_status": rng.choices(["authorized", "captured", "failed", "refunded"], weights=[8, 82, 7, 3])[
                    0
                ],
                "amount": round(row.net, 2),
            }
        )
    return pd.DataFrame(rows)


def _generate_shipments(rng: random.Random, orders: pd.DataFrame, warehouses: pd.DataFrame) -> pd.DataFrame:
    warehouse_ids = warehouses["warehouse_id"].tolist()
    rows = []
    shipped_orders = orders[orders["status"].isin(["shipped", "delivered", "returned"])]
    for index, order in enumerate(shipped_orders.itertuples(index=False), start=1):
        ordered_at = datetime.fromisoformat(order.order_ts)
        ship_ts = ordered_at + timedelta(hours=rng.randint(4, 72))
        promised = ordered_at + timedelta(days=rng.choice([2, 3, 4, 5]))
        delivered = ship_ts + timedelta(hours=rng.randint(8, 120))
        rows.append(
            {
                "shipment_id": _id("ship", index),
                "order_id": order.order_id,
                "warehouse_id": rng.choice(warehouse_ids),
                "ship_ts": ship_ts.isoformat(),
                "promised_delivery_ts": promised.isoformat(),
                "delivered_ts": delivered.isoformat(),
                "carrier": rng.choice(["Bosta", "Aramex", "DHL", "Internal Fleet"]),
                "shipping_cost": round(rng.uniform(25, 250), 2),
            }
        )
    return pd.DataFrame(rows)


def _generate_returns(rng: random.Random, order_items: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    returned_order_ids = set(orders.loc[orders["status"] == "returned", "order_id"])
    eligible = order_items[order_items["order_id"].isin(returned_order_ids)]
    rows = []
    for index, item in enumerate(eligible.itertuples(index=False), start=1):
        if rng.random() > 0.6:
            continue
        rows.append(
            {
                "return_id": _id("ret", index),
                "order_item_id": item.order_item_id,
                "return_ts": (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=rng.randint(0, 120))).isoformat(),
                "reason": rng.choice(["damaged", "wrong_item", "late_delivery", "changed_mind", "quality"]),
                "refund_amount": round(item.quantity * item.unit_price * (1 - item.discount_pct), 2),
            }
        )
    return pd.DataFrame(rows)


def _inject_dirty_records(tables: dict[str, pd.DataFrame], profile: DataProfile) -> dict[str, int]:
    dirty_counts: dict[str, int] = {}
    if profile.customers:
        duplicate = tables["customers"].iloc[[0]].copy()
        duplicate.loc[:, "email"] = "duplicate@example.com"
        tables["customers"] = pd.concat([tables["customers"], duplicate], ignore_index=True)
        dirty_counts["duplicate_customer_id"] = len(duplicate)
    if profile.products:
        bad_product = tables["products"].iloc[[0]].copy()
        bad_product.loc[:, "product_id"] = "prod_bad_negative_cost"
        bad_product.loc[:, "unit_cost"] = -10
        tables["products"] = pd.concat([tables["products"], bad_product], ignore_index=True)
        dirty_counts["negative_product_cost"] = 1
    if profile.orders:
        tables["orders"].loc[0, "customer_id"] = "cust_missing_999"
        duplicate_order = tables["orders"].iloc[[1]].copy()
        tables["orders"] = pd.concat([tables["orders"], duplicate_order], ignore_index=True)
        dirty_counts["missing_order_customer"] = 1
        dirty_counts["duplicate_order_id"] = 1
    if not tables["order_items"].empty:
        tables["order_items"].loc[0, "quantity"] = -2
        dirty_counts["negative_order_item_quantity"] = 1
    if not tables["payments"].empty:
        tables["payments"].loc[0, "payment_status"] = "mystery_status"
        dirty_counts["invalid_payment_status"] = 1
    return dirty_counts


def _write_web_events(
    profile: DataProfile,
    rng: random.Random,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    path: Path,
    base_date: datetime,
) -> int:
    customer_ids = customers["customer_id"].tolist()
    product_ids = products["product_id"].tolist()
    written = 0
    with path.open("w", encoding="utf-8") as handle:
        for chunk_start in range(0, profile.web_events, profile.event_chunk_size):
            chunk_end = min(chunk_start + profile.event_chunk_size, profile.web_events)
            for index in range(chunk_start + 1, chunk_end + 1):
                customer_id = rng.choice(customer_ids)
                session_id = f"sess_{rng.randint(1, max(1, profile.web_events // 4)):08d}"
                event_ts = _rand_date(rng, base_date, 500)
                if index == 1:
                    event_ts = base_date - timedelta(days=30)
                event = {
                    "event_id": _stable_event_id(session_id, index),
                    "customer_id": customer_id,
                    "session_id": session_id,
                    "event_ts": event_ts.isoformat(),
                    "event_type": rng.choices(EVENT_TYPES, weights=[45, 28, 12, 5, 3, 7])[0],
                    "product_id": rng.choice(product_ids),
                    "device": rng.choice(["ios", "android", "web", "mobile_web"]),
                    "campaign": rng.choice(CHANNELS),
                }
                handle.write(json.dumps(event) + "\n")
                written += 1
    return written
