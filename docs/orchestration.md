# Orchestration

Airflow DAG: `airflow/dags/ecommerce_platform_dag.py`

Task order:

1. `generate-batch`
2. `stream-produce`
3. `stream-consume`
4. `run-spark`
5. `run-dbt`
6. `run-quality`

The CLI mirrors the same flow:

```bash
commerce-platform run-all --profile ci
commerce-platform smoke --profile ci
```

Profiles:

| Profile | Purpose |
| --- | --- |
| ci | Fast tests and clean clone smoke runs. |
| demo | Dashboard demos and screenshots. |
| full | Large-scale synthetic run: 250k+ orders and 5M+ events. |
