with customers as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/customers/*.parquet')
),

orders as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/orders/*.parquet')
),

order_items as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/order_items/*.parquet')
)

select
    c.customer_id,
    c.region,
    c.acquisition_channel,
    c.loyalty_tier,
    count(distinct o.order_id) as orders,
    round(coalesce(sum(i.net_sales), 0), 2) as lifetime_revenue,
    round(coalesce(avg(i.net_sales), 0), 2) as avg_item_revenue,
    max(o.order_date) as last_order_date
from customers as c
left join orders as o on c.customer_id = o.customer_id and o.status <> 'cancelled'
left join order_items as i on o.order_id = i.order_id
group by 1, 2, 3, 4
