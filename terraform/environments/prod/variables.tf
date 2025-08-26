# 프로덕션 환경 변수

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "global-dual-nova-chatbot"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "ecs_cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 1024  # 프로덕션 환경에서는 더 많은 리소스 사용
}

variable "ecs_memory" {
  description = "Memory (MB) for ECS task"
  type        = number
  default     = 2048  # 프로덕션 환경에서는 더 많은 리소스 사용
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2  # 프로덕션에서는 고가용성을 위해 최소 2개
}

variable "ecs_min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 10  # 프로덕션 환경에서는 더 큰 스케일
}

variable "knowledge_base_id" {
  description = "Amazon Bedrock Knowledge Base ID"
  type        = string
  
  validation {
    condition     = length(var.knowledge_base_id) > 0
    error_message = "Knowledge Base ID must be provided for production environment."
  }
}

variable "data_source_ids" {
  description = "List of data source IDs for the Knowledge Base"
  type        = list(string)
  default     = []
}

variable "notion_token" {
  description = "Notion API token"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.notion_token) > 0
    error_message = "Notion token must be provided for production environment."
  }
}

variable "container_image" {
  description = "Container image for ECS task"
  type        = string
  default     = "python:3.11-slim"
}

variable "enable_auto_scaling" {
  description = "Enable ECS auto scaling"
  type        = bool
  default     = true  # 프로덕션 환경에서는 활성화
}

variable "auto_scaling_target_cpu" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 60  # 프로덕션에서는 더 낮은 임계값
}

variable "auto_scaling_target_memory" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 70  # 프로덕션에서는 더 낮은 임계값
}

variable "enable_logging" {
  description = "Enable CloudWatch logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30  # 프로덕션 환경에서는 더 긴 보존 기간
}

variable "enable_https" {
  description = "Enable HTTPS on ALB (requires SSL certificate)"
  type        = bool
  default     = true  # 프로덕션 환경에서는 HTTPS 필수
}

variable "ssl_certificate_arn" {
  description = "SSL certificate ARN for HTTPS"
  type        = string
  
  validation {
    condition = var.enable_https == false || length(var.ssl_certificate_arn) > 0
    error_message = "SSL certificate ARN must be provided when HTTPS is enabled in production."
  }
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {
    Environment = "prod"
    Purpose     = "production"
    Backup      = "required"
    Monitoring  = "enabled"
  }
}

variable "owner" {
  description = "Owner of the resources (for tagging and cost allocation)"
  type        = string
  default     = "DevOps-Team"
}

variable "cost_center" {
  description = "Cost center for billing and cost allocation"
  type        = string
  default     = "Engineering-Prod"
}