# 개발 환경 출력

# Application URLs
output "application_url" {
  description = "URL to access the application"
  value       = var.enable_https ? "https://${module.compute.load_balancer_dns_name}" : "http://${module.compute.load_balancer_dns_name}"
}

output "application_urls" {
  description = "All available URLs to access the application"
  value = {
    http  = "http://${module.compute.load_balancer_dns_name}"
    https = var.enable_https ? "https://${module.compute.load_balancer_dns_name}" : "HTTPS not enabled"
  }
}

# Load Balancer Information
output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.compute.load_balancer_dns_name
}

output "load_balancer_zone_id" {
  description = "Hosted zone ID of the load balancer"
  value       = module.compute.load_balancer_zone_id
}

# ECS Information
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.compute.ecs_cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.compute.ecs_service_name
}

# VPC Information
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

# Security Information
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = module.security.alb_security_group_id
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = module.security.ecs_security_group_id
}

# Storage Information
output "code_bucket_name" {
  description = "Name of the S3 bucket for application code"
  value       = module.storage.code_bucket_name
}

output "alb_logs_bucket_name" {
  description = "Name of the S3 bucket for ALB logs"
  value       = module.storage.alb_logs_bucket_name
}

# Secrets Information
output "app_config_secret_arn" {
  description = "ARN of the application configuration secret"
  value       = module.storage.app_config_secret_arn
}

output "notion_token_secret_arn" {
  description = "ARN of the Notion token secret"
  value       = module.storage.notion_token_secret_arn
}

# CloudWatch Information
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.compute.cloudwatch_log_group_name
}

# Development Environment Information
output "dev_environment_info" {
  description = "Development environment information and next steps"
  value = {
    environment = "development"
    region = var.aws_region
    project_name = var.project_name
    access_url = "http://${module.compute.load_balancer_dns_name}"
    resource_prefix = "${var.project_name}-dev"
    cost_optimization = {
      cpu_units = var.ecs_cpu
      memory_mb = var.ecs_memory
      auto_scaling_enabled = var.enable_auto_scaling
      log_retention_days = var.log_retention_days
    }
    next_steps = [
      "1. Access the application using: http://${module.compute.load_balancer_dns_name}",
      "2. Configure your Knowledge Base ID: ${var.knowledge_base_id}",
      "3. Test the chatbot functionality",
      "4. Monitor logs in CloudWatch: ${module.compute.cloudwatch_log_group_name}",
      "5. Scale up resources for production deployment"
    ]
  }
}