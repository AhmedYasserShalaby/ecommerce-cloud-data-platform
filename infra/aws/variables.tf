variable "aws_region" {
  description = "AWS region for the optional cloud deployment."
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Project name prefix."
  type        = string
  default     = "ecommerce-cloud-data-platform"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
}
