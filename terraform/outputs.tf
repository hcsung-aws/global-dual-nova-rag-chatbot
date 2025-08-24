output "application_url" {
  description = "Application Load Balancer URL"
  value       = "http://${aws_lb.main.dns_name}"
}

output "application_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.main.dns_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.main.name
}

output "s3_bucket_name" {
  description = "S3 bucket name for code storage"
  value       = aws_s3_bucket.code.bucket
}

output "secrets_manager_arns" {
  description = "Secrets Manager ARNs"
  value = {
    app_config    = aws_secretsmanager_secret.app_config.arn
    notion_token  = aws_secretsmanager_secret.notion_token.arn
  }
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = var.enable_logging ? aws_cloudwatch_log_group.ecs[0].name : null
}

output "iam_role_arns" {
  description = "IAM role ARNs"
  value = {
    task_execution = aws_iam_role.ecs_task_execution.arn
    task_role      = aws_iam_role.ecs_task.arn
  }
}

output "security_group_ids" {
  description = "Security group IDs"
  value = {
    alb = aws_security_group.alb.id
    ecs = aws_security_group.ecs.id
  }
}

output "deployment_instructions" {
  description = "Post-deployment instructions"
  value = <<-EOT
    Deployment completed successfully!
    
    1. Application URL: http://${aws_lb.main.dns_name}
    2. Update your Knowledge Base ID in Secrets Manager if needed
    3. Upload your application code to S3 bucket: ${aws_s3_bucket.code.bucket}
    4. Monitor the application in CloudWatch logs: ${var.enable_logging ? aws_cloudwatch_log_group.ecs[0].name : "N/A"}
    
    Next steps:
    - Configure your Knowledge Base data sources
    - Test the application with sample queries
    - Set up monitoring and alerts
    - Configure auto-scaling policies if needed
  EOT
}
