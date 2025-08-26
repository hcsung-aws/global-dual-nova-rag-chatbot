# 프로덕션 환경 출력

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

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = module.compute.load_balancer_arn
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

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = module.compute.ecs_task_definition_arn
}

# VPC Information
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.networking.vpc_cidr_block
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

# Production Environment Information
output "production_environment_info" {
  description = "Production environment information and operational details"
  value = {
    environment = "production"
    region = var.aws_region
    project_name = var.project_name
    access_url = var.enable_https ? "https://${module.compute.load_balancer_dns_name}" : "http://${module.compute.load_balancer_dns_name}"
    resource_prefix = "${var.project_name}-prod"
    high_availability = {
      desired_tasks = var.ecs_desired_count
      min_tasks = var.ecs_min_capacity
      max_tasks = var.ecs_max_capacity
      auto_scaling_enabled = var.enable_auto_scaling
      multi_az_deployment = true
    }
    security = {
      https_enabled = var.enable_https
      ssl_certificate = var.ssl_certificate_arn != "" ? "configured" : "not configured"
      secrets_manager = "enabled"
      private_subnets = "enabled"
    }
    monitoring = {
      cloudwatch_logs = var.enable_logging
      log_retention_days = var.log_retention_days
      container_insights = "enabled"
      alb_access_logs = "enabled"
    }
    operational_notes = [
      "🔒 Production environment with enhanced security",
      "📊 Auto-scaling enabled for high availability",
      "🔍 Comprehensive monitoring and logging configured",
      "⚡ Optimized for performance and cost efficiency",
      "🛡️ SSL/TLS encryption enabled for secure communication"
    ]
  }
}

# Security Configuration Summary
output "security_configuration" {
  description = "Security configuration summary for production"
  value = {
    https_enabled = var.enable_https
    ssl_certificate_configured = var.ssl_certificate_arn != ""
    secrets_manager_integration = "enabled"
    private_subnet_deployment = "enabled"
    security_groups_configured = "enabled"
    iam_roles_least_privilege = "enabled"
  }
}