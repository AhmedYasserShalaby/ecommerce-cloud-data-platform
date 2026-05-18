terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

locals {
  prefix = "${var.project_name}-${var.environment}-${data.aws_caller_identity.current.account_id}"
  lake_zones = toset(["raw", "bronze", "silver", "gold", "logs"])
}

resource "aws_s3_bucket" "lake" {
  for_each = local.lake_zones
  bucket   = "${local.prefix}-${each.key}"
}

resource "aws_s3_bucket_versioning" "lake" {
  for_each = aws_s3_bucket.lake
  bucket   = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake" {
  for_each = aws_s3_bucket.lake
  bucket   = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lake" {
  for_each                = aws_s3_bucket.lake
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_glue_catalog_database" "commerce" {
  name        = "${var.project_name}_${var.environment}"
  description = "Catalog database for ecommerce cloud data platform lakehouse tables."
}

resource "aws_athena_workgroup" "commerce" {
  name = "${var.project_name}-${var.environment}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.lake["logs"].bucket}/athena-results/"
    }
  }
}

resource "aws_cloudwatch_log_group" "platform" {
  name              = "/data-platform/${var.project_name}/${var.environment}"
  retention_in_days = 30
}

data "aws_iam_policy_document" "platform_least_privilege" {
  statement {
    sid = "LakeReadWrite"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = concat(
      [for bucket in aws_s3_bucket.lake : bucket.arn],
      [for bucket in aws_s3_bucket.lake : "${bucket.arn}/*"],
    )
  }

  statement {
    sid = "GlueAthenaAccess"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:CreateTable",
      "glue:UpdateTable",
      "athena:StartQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "WritePlatformLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.platform.arn}:*"]
  }
}

resource "aws_iam_policy" "platform" {
  name        = "${var.project_name}-${var.environment}-policy"
  description = "Least-privilege policy for ecommerce cloud data platform jobs."
  policy      = data.aws_iam_policy_document.platform_least_privilege.json
}
