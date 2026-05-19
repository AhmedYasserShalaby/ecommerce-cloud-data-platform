# Data Quality and Observability Report

Profile: `ci`
Platform score: **100.0%**

## Checks

| check_name                                 | passed   | observed                   | expected   |
|:-------------------------------------------|:---------|:---------------------------|:-----------|
| contract_quality_floor                     | True     | 96.15                      | >= 95      |
| required_export:mart_revenue_daily.csv     | True     | mart_revenue_daily.csv     | present    |
| required_export:mart_customer_ltv.csv      | True     | mart_customer_ltv.csv      | present    |
| required_export:mart_funnel_conversion.csv | True     | mart_funnel_conversion.csv | present    |
| required_export:mart_fulfillment_sla.csv   | True     | mart_fulfillment_sla.csv   | present    |
| required_export:contract_summary.csv       | True     | contract_summary.csv       | present    |
| required_export:silver_manifest.csv        | True     | silver_manifest.csv        | present    |
| required_export:gold_manifest.csv          | True     | gold_manifest.csv          | present    |
| gold_mart_count                            | True     | 9                          | >= 9       |
| late_event_rate                            | True     | 0.0004                     | <= 0.05    |
| positive_revenue                           | True     | 2738512.51                 | > 0        |
| sla_rate_bounds                            | True     | 0..1                       | all rows   |

## Failed Checks

No failed checks.
