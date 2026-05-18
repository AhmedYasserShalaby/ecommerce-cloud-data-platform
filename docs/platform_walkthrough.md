# Platform Walkthrough

## Overview

This project is an end-to-end e-commerce data platform:

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

## Technical Summary

The platform processes 250k+ orders and 5M+ events in the full profile through batch and streaming ingestion into bronze, silver, and gold lakehouse layers, with DuckDB/dbt marts, Airflow orchestration, quality checks, freshness monitoring, Docker, Terraform, CI, and a Streamlit platform console.
