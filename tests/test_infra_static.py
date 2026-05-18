from __future__ import annotations

from pathlib import Path


def test_terraform_maps_expected_aws_services():
    main = Path("infra/aws/main.tf").read_text()
    assert "aws_s3_bucket" in main
    assert "aws_glue_catalog_database" in main
    assert "aws_athena_workgroup" in main
    assert "aws_iam_policy" in main
    assert "aws_cloudwatch_log_group" in main
