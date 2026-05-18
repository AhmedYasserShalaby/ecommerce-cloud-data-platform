# AWS Mapping

The local implementation is the required proof. Terraform shows how it maps to AWS.

| Local component | AWS target |
| --- | --- |
| Raw files | S3 raw bucket |
| Bronze Parquet | S3 bronze bucket |
| Silver Parquet | S3 silver bucket |
| Gold marts | S3 gold bucket + Athena |
| Metadata | Glue Data Catalog |
| Observability | CloudWatch + S3 logs |
| Permissions | IAM least-privilege policy |

The Terraform module is in `infra/aws`.

No AWS credentials are needed to run the project locally.
