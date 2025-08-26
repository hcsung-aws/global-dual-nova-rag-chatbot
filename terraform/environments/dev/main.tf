# 개발 환경 설정

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

# 데이터 소스
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# 로컬 변수
locals {
  environment = "dev"
  resource_prefix = "${var.project_name}-${local.environment}"
  
  common_tags = merge(var.tags, {
    Project      = var.project_name
    Environment  = local.environment
    ManagedBy    = "Terraform"
    Owner        = var.owner
    CostCenter   = var.cost_center
    CreatedDate  = formatdate("YYYY-MM-DD", timestamp())
    Application  = "global-dual-nova-rag-chatbot"
  })
}

# 스토리지 모듈
module "storage" {
  source = "../../modules/storage"

  resource_prefix           = local.resource_prefix
  common_tags              = local.common_tags
  aws_region               = var.aws_region
  environment              = local.environment
  account_id               = data.aws_caller_identity.current.account_id
  knowledge_base_id        = var.knowledge_base_id
  data_source_ids          = var.data_source_ids
  notion_token             = var.notion_token
  chatbot_app_source_path  = "${path.module}/../../../src/chatbot_app.py"
  requirements_source_path = "${path.module}/../../../config/requirements.txt"
}

# 네트워킹 모듈
module "networking" {
  source = "../../modules/networking"

  resource_prefix        = local.resource_prefix
  common_tags           = local.common_tags
  vpc_cidr              = var.vpc_cidr
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  availability_zones    = data.aws_availability_zones.available.names
}

# 보안 모듈
module "security" {
  source = "../../modules/security"

  resource_prefix = local.resource_prefix
  common_tags     = local.common_tags
  vpc_id          = module.networking.vpc_id
  secrets_arns    = module.storage.secrets_arns
  s3_bucket_arns  = module.storage.s3_bucket_arns
}

# 컴퓨팅 모듈
module "compute" {
  source = "../../modules/compute"

  resource_prefix              = local.resource_prefix
  common_tags                 = local.common_tags
  aws_region                  = var.aws_region
  vpc_id                      = module.networking.vpc_id
  public_subnet_ids           = module.networking.public_subnet_ids
  private_subnet_ids          = module.networking.private_subnet_ids
  alb_security_group_id       = module.security.alb_security_group_id
  ecs_security_group_id       = module.security.ecs_security_group_id
  ecs_task_execution_role_arn = module.security.ecs_task_execution_role_arn
  ecs_task_role_arn          = module.security.ecs_task_role_arn
  ecs_cpu                    = var.ecs_cpu
  ecs_memory                 = var.ecs_memory
  ecs_desired_count          = var.ecs_desired_count
  ecs_min_capacity           = var.ecs_min_capacity
  ecs_max_capacity           = var.ecs_max_capacity
  container_image            = var.container_image
  code_bucket_name           = module.storage.code_bucket_name
  alb_logs_bucket_name       = module.storage.alb_logs_bucket_name
  notion_token_secret_arn    = module.storage.notion_token_secret_arn
  app_config_secret_arn      = module.storage.app_config_secret_arn
  enable_auto_scaling        = var.enable_auto_scaling
  auto_scaling_target_cpu    = var.auto_scaling_target_cpu
  auto_scaling_target_memory = var.auto_scaling_target_memory
  enable_logging             = var.enable_logging
  log_retention_days         = var.log_retention_days
  enable_https               = var.enable_https
  ssl_certificate_arn        = var.ssl_certificate_arn
}