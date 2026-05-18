with web_events as (
    select * from read_parquet('{{ var("silver_root", "../../data/lake/silver/profile=ci/run_date=2026-05-18") }}/web_events/*.parquet')
)

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
