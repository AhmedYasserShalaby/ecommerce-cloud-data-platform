# AWS Mapping

This Terraform module is **AWS-ready** but not required for the local proof.

Local platform mapping:

| Local layer | AWS service |
| --- | --- |
| `data/raw` | S3 raw bucket |
| `data/lake/bronze` | S3 bronze bucket |
| `data/lake/silver` | S3 silver bucket |
| `data/lake/gold` | S3 gold bucket |
| DuckDB/dbt marts | Athena + Glue |
| Quality reports | S3 logs bucket + CloudWatch |
| Job permissions | IAM least-privilege policy |

Dry review:

```bash
terraform init
terraform plan
```

No AWS credentials are needed for the main local project.
