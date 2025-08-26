# 보안 모듈 변수

variable "resource_prefix" {
  description = "Resource naming prefix"
  type        = string
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
}

variable "vpc_id" {
  description = "VPC ID where security groups will be created"
  type        = string
}

variable "secrets_arns" {
  description = "List of Secrets Manager ARNs for IAM policy"
  type        = list(string)
}

variable "s3_bucket_arns" {
  description = "List of S3 bucket ARNs for IAM policy"
  type        = list(string)
}