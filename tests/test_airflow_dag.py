from __future__ import annotations

import importlib.util
from pathlib import Path


def test_airflow_dag_definition_has_expected_commands():
    dag_path = Path("airflow/dags/ecommerce_platform_dag.py")
    spec = importlib.util.spec_from_file_location("ecommerce_platform_dag", dag_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.DAG_ID == "ecommerce_cloud_data_platform"
    assert module.COMMANDS[0].startswith("commerce-platform generate-batch")
    assert module.COMMANDS[-1].startswith("commerce-platform run-quality")
