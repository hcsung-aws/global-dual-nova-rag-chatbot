terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

# 표준화된 명명 규칙과 태그 시스템
locals {
  # 표준 명명 패턴: ${project_name}-${service}-${resource_type}-${environment}
  resource_prefix = "${var.project_name}-${var.environment}"
  
  # 표준화된 공통 태그
  common_tags = merge(var.tags, {
    Project      = var.project_name
    Environment  = var.environment
    ManagedBy    = "Terraform"
    Owner        = var.owner
    CostCenter   = var.cost_center
    CreatedDate  = formatdate("YYYY-MM-DD", timestamp())
    Application  = "global-dual-nova-rag-chatbot"
  })
  
  # 서비스별 명명 규칙
  naming = {
    vpc                = "${local.resource_prefix}-vpc"
    internet_gateway   = "${local.resource_prefix}-igw"
    public_subnet      = "${local.resource_prefix}-public-subnet"
    private_subnet     = "${local.resource_prefix}-private-subnet"
    nat_gateway        = "${local.resource_prefix}-nat-gateway"
    nat_eip           = "${local.resource_prefix}-nat-eip"
    public_route_table = "${local.resource_prefix}-public-rt"
    private_route_table = "${local.resource_prefix}-private-rt"
    alb_security_group = "${local.resource_prefix}-alb-sg"
    ecs_security_group = "${local.resource_prefix}-ecs-sg"
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = local.naming.vpc
    Type = "Network"
    Tier = "Infrastructure"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = local.naming.internet_gateway
    Type = "Network"
    Tier = "Infrastructure"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.naming.public_subnet}-${count.index + 1}"
    Type = "Network"
    Tier = "Public"
    SubnetType = "Public"
    AvailabilityZone = data.aws_availability_zones.available.names[count.index]
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.naming.private_subnet}-${count.index + 1}"
    Type = "Network"
    Tier = "Private"
    SubnetType = "Private"
    AvailabilityZone = data.aws_availability_zones.available.names[count.index]
  })
}

# NAT Gateway
resource "aws_eip" "nat" {
  count = length(aws_subnet.public)

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${local.naming.nat_eip}-${count.index + 1}"
    Type = "Network"
    Tier = "Infrastructure"
    AvailabilityZone = data.aws_availability_zones.available.names[count.index]
  })
}

resource "aws_nat_gateway" "main" {
  count = length(aws_subnet.public)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(local.common_tags, {
    Name = "${local.naming.nat_gateway}-${count.index + 1}"
    Type = "Network"
    Tier = "Infrastructure"
    AvailabilityZone = data.aws_availability_zones.available.names[count.index]
  })

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = local.naming.public_route_table
    Type = "Network"
    Tier = "Infrastructure"
    RouteType = "Public"
  })
}

resource "aws_route_table" "private" {
  count = length(aws_nat_gateway.main)

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = merge(local.common_tags, {
    Name = "${local.naming.private_route_table}-${count.index + 1}"
    Type = "Network"
    Tier = "Infrastructure"
    RouteType = "Private"
    AvailabilityZone = data.aws_availability_zones.available.names[count.index]
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "${local.resource_prefix}-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = local.naming.alb_security_group
    Type = "Security"
    Tier = "LoadBalancer"
    Service = "ALB"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "ecs" {
  name_prefix = "${local.resource_prefix}-ecs-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = local.naming.ecs_security_group
    Type = "Security"
    Tier = "Application"
    Service = "ECS"
  })

  lifecycle {
    create_before_destroy = true
  }
}
