# Data Model

## Sources

| Source | Description |
| --- | --- |
| customers | Customer profile, region, acquisition, loyalty tier. |
| products | SKU, category, brand, unit cost, unit price. |
| warehouses | Fulfillment node by region and capacity. |
| inventory | Product stock snapshot by warehouse. |
| orders | Order header, customer, status, region, timestamp. |
| order_items | Product-level order lines and discounts. |
| payments | Payment status, method, amount. |
| shipments | Carrier, delivery timestamps, cost, SLA. |
| returns | Return reason and refund amount. |
| web_events | Product views, carts, checkouts, purchases, campaigns. |

## Gold Marts

| Mart | Business question |
| --- | --- |
| mart_revenue_daily | How much revenue and margin did each region generate? |
| mart_product_performance | Which products drive units, revenue, and profit? |
| mart_inventory_risk | Which products are near reorder or stockout? |
| mart_customer_ltv | Which customers and channels drive lifetime revenue? |
| mart_funnel_conversion | Where do sessions convert or drop? |
| mart_fulfillment_sla | Which carriers meet delivery promise? |
| mart_returns | Which categories and reasons drive refunds? |
| mart_data_freshness | Are key sources fresh enough? |
| mart_pipeline_runs | Did the platform build expected outputs? |

## Privacy

Customer email is hashed in silver and not exposed in gold marts.
