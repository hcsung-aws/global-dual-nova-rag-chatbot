# 모듈화된 구조의 출력 파일

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

# Deployment Information
output "deployment_info" {
  description = "Deployment information and next steps"
  value = {
    environment = var.environment
    region = var.aws_region
    project_name = var.project_name
    resource_prefix = local.resource_prefix
    access_url = var.enable_https ? "https://${module.compute.load_balancer_dns_name}" : "http://${module.compute.load_balancer_dns_name}"
    
    architecture = {
      modular_design = "enabled"
      modules_used = ["networking", "security", "compute", "storage"]
      environment_specific = "supported"
    }
    
    standardization = {
      naming_convention = "${var.project_name}-${var.environment}-*"
      tagging_strategy = "comprehensive"
      resource_organization = "modular"
    }
    
    next_steps = [
      "1. Access the application using the URL above",
      "2. Configure your Knowledge Base ID in the application settings",
      "3. Test the chatbot functionality",
      "4. Monitor resources using standardized tags",
      "5. Scale to other environments using the modular structure"
    ]
  }
}

# Module Information
output "module_information" {
  description = "Information about the modular architecture"
  value = {
    networking_module = {
      vpc_id = module.networking.vpc_id
      public_subnets = length(module.networking.public_subnet_ids)
      private_subnets = length(module.networking.private_subnet_ids)
      nat_gateways = length(module.networking.nat_gateway_ids)
    }
    
    security_module = {
      security_groups = 2
      iam_roles = 2
      secrets_managed = length(module.storage.secrets_arns)
    }
    
    compute_module = {
      ecs_cluster = module.compute.ecs_cluster_name
      load_balancer = module.compute.load_balancer_dns_name
      auto_scaling = var.enable_auto_scaling
    }
    
    storage_module = {
      s3_buckets = 2
      secrets_manager = 2
      encryption = "enabled"
    }
  }
}