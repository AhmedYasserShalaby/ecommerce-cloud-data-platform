from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from commerce_platform.paths import get_paths
from commerce_platform.silver import latest_silver_partition, run_silver

GOLD_MARTS = [
    "mart_revenue_daily",
    "mart_product_performance",
    "mart_inventory_risk",
    "mart_customer_ltv",
    "mart_funnel_conversion",
    "mart_fulfillment_sla",
    "mart_returns",
    "mart_data_freshness",
    "mart_pipeline_runs",
]


def run_gold(profile: str = "ci", data_root: str | Path | None = None) -> dict[str, int]:
    paths = get_paths(data_root)
    run_silver(profile, paths.data_root)
    silver_root = latest_silver_partition(paths, profile)
    warehouse_path = paths.warehouse / "commerce.duckdb"
    paths.warehouse.mkdir(parents=True, exist_ok=True)
    gold_root = paths.zone("gold") / f"profile={profile}" / silver_root.name
    gold_root.mkdir(parents=True, exist_ok=True)
    paths.exports.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(warehouse_path))
    try:
        _register_silver_views(connection, silver_root)
        _build_marts(connection, profile, silver_root.name)
        counts = {}
        for mart in GOLD_MARTS:
            frame = connection.sql(f"select * from {mart}").df()
            frame.to_parquet(gold_root / f"{mart}.parquet", index=False)
            frame.to_csv(paths.exports / f"{mart}.csv", index=False)
            counts[mart] = len(frame)
        pd.DataFrame(
            [
                {
                    "profile": profile,
                    "run_partition": silver_root.name,
                    "mart_name": mart,
                    "row_count": count,
                }
                for mart, count in counts.items()
            ]
        ).to_csv(paths.exports / "gold_manifest.csv", index=False)
        return counts
    finally:
        connection.close()


def _register_silver_views(connection: duckdb.DuckDBPyConnection, silver_root: Path) -> None:
    for path in sorted(silver_root.glob("*/part-000.parquet")):
        table = path.parent.name
        connection.sql(f"create or replace view {table} as select * from read_parquet('{path.as_posix()}')")


def _build_marts(connection: duckdb.DuckDBPyConnection, profile: str, run_partition: str) -> None:
    connection.sql(
        """
        create or replace table mart_revenue_daily as
        select
            o.order_date,
            o.region,
            count(distinct o.order_id) as total_orders,
            count(distinct o.customer_id) as active_customers,
            round(sum(i.net_sales), 2) as revenue,
            round(sum(i.net_sales - (i.quantity * p.unit_cost)), 2) as gross_profit,
            round(sum(i.net_sales - (i.quantity * p.unit_cost)) / nullif(sum(i.net_sales), 0), 4) as gross_margin_pct,
            round(avg(i.net_sales), 2) as avg_item_revenue
        from orders o
        join order_items i on o.order_id = i.order_id
        join products p on i.product_id = p.product_id
        where o.status <> 'cancelled'
        group by 1, 2
        order by 1, 2
        """
    )
    connection.sql(
        """
        create or replace table mart_product_performance as
        select
            p.product_id,
            p.sku,
            p.category,
            count(distinct i.order_id) as orders,
            sum(i.quantity) as units_sold,
            round(sum(i.net_sales), 2) as revenue,
            round(sum(i.net_sales - (i.quantity * p.unit_cost)), 2) as gross_profit,
            round(avg(i.discount_pct), 4) as avg_discount_pct
        from products p
        left join order_items i on p.product_id = i.product_id
        group by 1, 2, 3
        order by revenue desc nulls last
        """
    )
    connection.sql(
        """
        create or replace table mart_inventory_risk as
        select
            inv.snapshot_date,
            inv.warehouse_id,
            w.region,
            inv.product_id,
            p.category,
            inv.on_hand_units,
            inv.reorder_point,
            inv.inventory_risk,
            case
                when inv.on_hand_units = 0 then 'stockout'
                when inv.inventory_risk then 'reorder'
                when inv.on_hand_units < inv.reorder_point * 2 then 'watch'
                else 'healthy'
            end as risk_band
        from inventory inv
        join warehouses w on inv.warehouse_id = w.warehouse_id
        join products p on inv.product_id = p.product_id
        order by inventory_risk desc, on_hand_units asc
        """
    )
    connection.sql(
        """
        create or replace table mart_customer_ltv as
        select
            c.customer_id,
            c.region,
            c.acquisition_channel,
            c.loyalty_tier,
            count(distinct o.order_id) as orders,
            round(coalesce(sum(i.net_sales), 0), 2) as lifetime_revenue,
            round(coalesce(avg(i.net_sales), 0), 2) as avg_item_revenue,
            max(o.order_date) as last_order_date
        from customers c
        left join orders o on c.customer_id = o.customer_id and o.status <> 'cancelled'
        left join order_items i on o.order_id = i.order_id
        group by 1, 2, 3, 4
        order by lifetime_revenue desc
        """
    )
    connection.sql(
        """
        create or replace table mart_funnel_conversion as
        select
            event_date,
            campaign,
            count(*) as events,
            count(distinct session_id) as sessions,
            sum(case when event_type = 'product_view' then 1 else 0 end) as product_views,
            sum(case when event_type = 'add_to_cart' then 1 else 0 end) as add_to_cart,
            sum(case when event_type = 'checkout_start' then 1 else 0 end) as checkout_starts,
            sum(case when event_type = 'purchase' then 1 else 0 end) as purchase_events,
            round(sum(case when event_type = 'purchase' then 1 else 0 end) / nullif(count(distinct session_id), 0), 4)
                as session_purchase_rate,
            sum(case when is_late_event then 1 else 0 end) as late_events
        from web_events
        group by 1, 2
        order by 1, 2
        """
    )
    connection.sql(
        """
        create or replace table mart_fulfillment_sla as
        select
            o.order_date,
            s.carrier,
            count(*) as shipments,
            round(avg(s.delivery_hours), 2) as avg_delivery_hours,
            round(sum(case when s.delivered_on_time then 1 else 0 end) / count(*), 4) as on_time_rate,
            round(sum(s.shipping_cost), 2) as shipping_cost
        from shipments s
        join orders o on s.order_id = o.order_id
        group by 1, 2
        order by 1, 2
        """
    )
    connection.sql(
        """
        create or replace table mart_returns as
        select
            p.category,
            r.reason,
            count(*) as returns,
            round(sum(r.refund_amount), 2) as refunded_amount,
            round(avg(r.refund_amount), 2) as avg_refund
        from returns r
        join order_items i on r.order_item_id = i.order_item_id
        join products p on i.product_id = p.product_id
        group by 1, 2
        order by refunded_amount desc
        """
    )
    connection.sql(
        f"""
        create or replace table mart_data_freshness as
        select * from (
            select '{profile}' as profile, '{run_partition}' as run_partition, 'orders' as source_name,
                max(order_ts) as max_observed_ts, count(*) as rows_loaded
            from orders
            union all
            select '{profile}' as profile, '{run_partition}' as run_partition, 'web_events' as source_name,
                max(event_ts) as max_observed_ts, count(*) as rows_loaded
            from web_events
            union all
            select '{profile}' as profile, '{run_partition}' as run_partition, 'payments' as source_name,
                max(payment_ts) as max_observed_ts, count(*) as rows_loaded
            from payments
        )
        order by source_name
        """
    )
    connection.sql(
        f"""
        create or replace table mart_pipeline_runs as
        select
            '{profile}' as profile,
            '{run_partition}' as run_partition,
            current_timestamp as built_at,
            (select count(*) from orders) as silver_orders,
            (select count(*) from web_events) as silver_events,
            (select round(sum(revenue), 2) from mart_revenue_daily) as gold_revenue,
            (select count(*) from mart_inventory_risk where inventory_risk) as inventory_risk_items,
            (select count(*) from mart_funnel_conversion where late_events > 0) as late_event_partitions
        """
    )
