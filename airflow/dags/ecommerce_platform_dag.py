from __future__ import annotations

from datetime import datetime

DAG_ID = "ecommerce_cloud_data_platform"
COMMANDS = [
    "commerce-platform generate-batch --profile demo",
    "commerce-platform stream-produce --profile demo --events 5000",
    "commerce-platform stream-consume --profile demo",
    "commerce-platform run-spark --profile demo",
    "commerce-platform run-dbt --profile demo",
    "commerce-platform run-quality --profile demo",
]

try:
    from airflow.operators.bash import BashOperator

    from airflow import DAG

    with DAG(
        dag_id=DAG_ID,
        description="Daily ecommerce cloud data platform batch, streaming, mart, and quality run.",
        start_date=datetime(2026, 5, 18),
        schedule="@daily",
        catchup=False,
        tags=["portfolio", "ecommerce", "data-platform"],
    ) as dag:
        tasks = [
            BashOperator(
                task_id=command.split()[1].replace("-", "_"),
                bash_command=f"cd /opt/airflow/project && {command}",
            )
            for command in COMMANDS
        ]
        for upstream, downstream in zip(tasks, tasks[1:], strict=False):
            upstream >> downstream
except Exception:
    dag = None
