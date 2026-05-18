# Recruiter Walkthrough

## What This Proves

This is not only a dashboard. It is an end-to-end data platform:

- source generation with dirty operational data
- contract validation and rejected rows
- bronze/silver/gold lakehouse layers
- streaming micro-batches with checkpointing
- DuckDB marts for business metrics
- Airflow orchestration
- quality and freshness observability
- AWS-ready infrastructure mapping

## Fast Demo

```bash
pip install -e ".[dev]"
commerce-platform smoke --profile ci
streamlit run app/streamlit_console.py
```

## Best CV Description

Built a hybrid local/AWS-ready e-commerce data platform processing 250k+ orders and 5M+ events through batch and streaming ingestion into bronze, silver, and gold lakehouse layers, with DuckDB/dbt marts, Airflow orchestration, quality checks, freshness monitoring, Docker, Terraform, CI, and a Streamlit platform console.
