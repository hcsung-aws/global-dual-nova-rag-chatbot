variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
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
  default     = 512
}

variable "ecs_memory" {
  description = "Memory (MB) for ECS task"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "ecs_min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 10
}

variable "knowledge_base_id" {
  description = "Amazon Bedrock Knowledge Base ID"
  type        = string
  default     = ""
  
  validation {
    condition     = length(var.knowledge_base_id) > 0
    error_message = "Knowledge Base ID must be provided. Create a Knowledge Base in Amazon Bedrock first."
  }
}

variable "data_source_ids" {
  description = "List of data source IDs for the Knowledge Base"
  type        = list(string)
  default     = []
}

variable "notion_token" {
  description = "Notion API token (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "container_image" {
  description = "Container image for ECS task"
  type        = string
  default     = "python:3.11-slim"
}

variable "enable_auto_scaling" {
  description = "Enable ECS auto scaling"
  type        = bool
  default     = true
}

variable "auto_scaling_target_cpu" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

variable "auto_scaling_target_memory" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80
}

variable "enable_logging" {
  description = "Enable CloudWatch logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "enable_https" {
  description = "Enable HTTPS on ALB (requires SSL certificate)"
  type        = bool
  default     = false
}

variable "ssl_certificate_arn" {
  description = "SSL certificate ARN for HTTPS"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

variable "owner" {
  description = "Owner of the resources (for tagging and cost allocation)"
  type        = string
  default     = "DevOps-Team"
  
  validation {
    condition     = length(var.owner) > 0
    error_message = "Owner must be specified for proper resource management."
  }
}

variable "cost_center" {
  description = "Cost center for billing and cost allocation"
  type        = string
  default     = "Engineering"
  
  validation {
    condition     = length(var.cost_center) > 0
    error_message = "Cost center must be specified for proper cost allocation."
  }
}

# Security and Access Control Variables
variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]
  
  validation {
    condition = length(var.allowed_cidr_blocks) > 0
    error_message = "At least one CIDR block must be specified."
  }
}

variable "restrict_public_access" {
  description = "Whether to restrict public access (recommended for production)"
  type        = bool
  default     = false
}

variable "admin_ip_addresses" {
  description = "List of admin IP addresses for restricted access (when restrict_public_access is true)"
  type        = list(string)
  default     = []
  
  validation {
    condition = var.restrict_public_access == false || length(var.admin_ip_addresses) > 0
    error_message = "Admin IP addresses must be provided when restrict_public_access is true."
  }
}

variable "enable_vpc_access" {
  description = "Allow access from VPC CIDR (useful for internal testing)"
  type        = bool
  default     = false
}

variable "custom_access_rules" {
  description = "Custom access rules for fine-grained control"
  type = list(object({
    description = string
    cidr_block  = string
    from_port   = number
    to_port     = number
    protocol    = string
  }))
  default = []
}
