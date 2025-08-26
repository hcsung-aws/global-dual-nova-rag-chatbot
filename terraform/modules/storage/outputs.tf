# 스토리지 모듈 출력

output "code_bucket_name" {
  description = "Name of the S3 bucket for application code"
  value       = aws_s3_bucket.code.bucket
}

output "code_bucket_arn" {
  description = "ARN of the S3 bucket for application code"
  value       = aws_s3_bucket.code.arn
}

output "alb_logs_bucket_name" {
  description = "Name of the S3 bucket for ALB logs"
  value       = aws_s3_bucket.alb_logs.bucket
}

output "alb_logs_bucket_arn" {
  description = "ARN of the S3 bucket for ALB logs"
  value       = aws_s3_bucket.alb_logs.arn
}

output "app_config_secret_arn" {
  description = "ARN of the application configuration secret"
  value       = aws_secretsmanager_secret.app_config.arn
}

output "notion_token_secret_arn" {
  description = "ARN of the Notion token secret"
  value       = aws_secretsmanager_secret.notion_token.arn
}

output "s3_bucket_arns" {
  description = "List of all S3 bucket ARNs"
  value       = [
    aws_s3_bucket.code.arn,
    aws_s3_bucket.alb_logs.arn
  ]
}

output "secrets_arns" {
  description = "List of all Secrets Manager ARNs"
  value       = [
    aws_secretsmanager_secret.app_config.arn,
    aws_secretsmanager_secret.notion_token.arn
  ]
}