# 네트워킹 모듈 - VPC, 서브넷, 라우팅 테이블, NAT 게이트웨이

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-vpc"
    Type = "Network"
    Tier = "Infrastructure"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-igw"
    Type = "Network"
    Tier = "Infrastructure"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-public-subnet-${count.index + 1}"
    Type = "Network"
    Tier = "Public"
    SubnetType = "Public"
    AvailabilityZone = var.availability_zones[count.index]
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-private-subnet-${count.index + 1}"
    Type = "Network"
    Tier = "Private"
    SubnetType = "Private"
    AvailabilityZone = var.availability_zones[count.index]
  })
}

# NAT Gateway EIPs
resource "aws_eip" "nat" {
  count = length(aws_subnet.public)

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-nat-eip-${count.index + 1}"
    Type = "Network"
    Tier = "Infrastructure"
    AvailabilityZone = var.availability_zones[count.index]
  })
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = length(aws_subnet.public)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-nat-gateway-${count.index + 1}"
    Type = "Network"
    Tier = "Infrastructure"
    AvailabilityZone = var.availability_zones[count.index]
  })

  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-public-rt"
    Type = "Network"
    Tier = "Infrastructure"
    RouteType = "Public"
  })
}

# Private Route Tables
resource "aws_route_table" "private" {
  count = length(aws_nat_gateway.main)

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-private-rt-${count.index + 1}"
    Type = "Network"
    Tier = "Infrastructure"
    RouteType = "Private"
    AvailabilityZone = var.availability_zones[count.index]
  })
}

# Route Table Associations - Public
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route Table Associations - Private
resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}