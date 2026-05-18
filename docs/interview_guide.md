# Interview Guide

## How To Explain It

"I built this to show I can move beyond one-off dashboards. It simulates an e-commerce company with orders, payments, shipments, inventory, returns, and web events. The platform lands raw data, validates contracts, creates clean silver entities, builds DuckDB gold marts, tracks quality and freshness, and exposes a Streamlit console."

## Likely Questions

| Question | Strong answer |
| --- | --- |
| Why synthetic data? | Safe to publish, deterministic, and intentionally dirty for validation. |
| Why DuckDB? | Fast local warehouse, SQL-friendly, easy CI, maps to Athena/BigQuery/Snowflake concepts. |
| Why Spark-compatible instead of only pandas? | The transforms are isolated like Spark jobs and Docker includes Java/PySpark path, while CI stays lightweight. |
| How do you avoid duplicate streaming events? | Consumer checkpoint offsets and event IDs; re-run consumes only new events. |
| What would you improve in production? | Managed orchestration, object storage, catalog tables, alerting, cost monitoring, and secrets manager. |
