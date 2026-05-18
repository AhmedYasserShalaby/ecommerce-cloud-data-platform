with orders as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/orders/*.parquet')
),

shipments as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/shipments/*.parquet')
)

select
    o.order_date,
    s.carrier,
    count(*) as shipments,
    round(avg(s.delivery_hours), 2) as avg_delivery_hours,
    round(sum(case when s.delivered_on_time then 1 else 0 end) / count(*), 4) as on_time_rate,
    round(sum(s.shipping_cost), 2) as shipping_cost
from shipments as s
join orders as o on s.order_id = o.order_id
group by 1, 2
