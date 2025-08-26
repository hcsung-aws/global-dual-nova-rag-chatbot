# Load Balancer Outputs
output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_zone_id" {
  description = "Hosted zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

# Application URLs
output "application_url" {
  description = "URL to access the application"
  value       = var.enable_https ? "https://${aws_lb.main.dns_name}" : "http://${aws_lb.main.dns_name}"
}

output "application_urls" {
  description = "All available URLs to access the application"
  value = {
    http  = "http://${aws_lb.main.dns_name}"
    https = var.enable_https ? "https://${aws_lb.main.dns_name}" : "HTTPS not enabled"
  }
}

# Security Information
output "security_configuration" {
  description = "Security configuration summary"
  value = {
    restricted_access = var.restrict_public_access
    allowed_ips = var.restrict_public_access ? var.admin_ip_addresses : ["Public access enabled"]
    vpc_access_enabled = var.enable_vpc_access
    https_enabled = var.enable_https
  }
}

# ECS Information
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.main.name
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = aws_ecs_task_definition.main.arn
}

# VPC Information
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

# Security Group Information
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = aws_security_group.ecs_tasks.id
}

# S3 Bucket Information
output "alb_logs_bucket_name" {
  description = "Name of the S3 bucket for ALB logs"
  value       = aws_s3_bucket.alb_logs.bucket
}

output "code_bucket_name" {
  description = "Name of the S3 bucket for application code"
  value       = aws_s3_bucket.code.bucket
}

# CloudWatch Information
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = var.enable_logging ? aws_cloudwatch_log_group.main[0].name : "Logging not enabled"
}

# Secrets Manager Information
output "app_config_secret_arn" {
  description = "ARN of the application configuration secret"
  value       = aws_secretsmanager_secret.app_config.arn
}

output "notion_token_secret_arn" {
  description = "ARN of the Notion token secret"
  value       = var.notion_token != "" ? aws_secretsmanager_secret.notion_token[0].arn : "Notion integration not configured"
}

# Deployment Information
output "deployment_info" {
  description = "Deployment information and next steps"
  value = {
    region = var.aws_region
    environment = var.environment
    project_name = var.project_name
    access_url = var.enable_https ? "https://${aws_lb.main.dns_name}" : "http://${aws_lb.main.dns_name}"
    security_note = var.restrict_public_access ? "Access restricted to specified IPs" : "⚠️  PUBLIC ACCESS ENABLED - Consider restricting access for production"
    next_steps = [
      "1. Access the application using the URL above",
      "2. Configure your Knowledge Base ID in the application settings",
      "3. Test the chatbot functionality",
      var.restrict_public_access ? "4. Verify access is properly restricted" : "4. ⚠️  IMPORTANT: Restrict access for production use"
    ]
  }
}
