output "lake_buckets" {
  description = "S3 buckets mapped to local raw/bronze/silver/gold/log zones."
  value       = { for zone, bucket in aws_s3_bucket.lake : zone => bucket.bucket }
}

output "glue_database" {
  description = "Glue database for lakehouse tables."
  value       = aws_glue_catalog_database.commerce.name
}

output "athena_workgroup" {
  description = "Athena workgroup for BI queries."
  value       = aws_athena_workgroup.commerce.name
}

output "platform_policy_arn" {
  description = "IAM policy ARN for platform jobs."
  value       = aws_iam_policy.platform.arn
}
