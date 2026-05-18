with orders as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/orders/*.parquet')
),

order_items as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/order_items/*.parquet')
),

products as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/products/*.parquet')
)

select
    o.order_date,
    o.region,
    count(distinct o.order_id) as total_orders,
    count(distinct o.customer_id) as active_customers,
    round(sum(i.net_sales), 2) as revenue,
    round(sum(i.net_sales - (i.quantity * p.unit_cost)), 2) as gross_profit,
    round(sum(i.net_sales - (i.quantity * p.unit_cost)) / nullif(sum(i.net_sales), 0), 4) as gross_margin_pct,
    round(avg(i.net_sales), 2) as avg_item_revenue
from orders as o
join order_items as i on o.order_id = i.order_id
join products as p on i.product_id = p.product_id
where o.status <> 'cancelled'
group by 1, 2
