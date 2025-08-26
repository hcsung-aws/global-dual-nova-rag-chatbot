# Application Load Balancer Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  vpc_id      = aws_vpc.main.id

  # Dynamic ingress rules based on configuration
  dynamic "ingress" {
    for_each = var.restrict_public_access ? [] : [1]
    content {
      description = "HTTP from allowed CIDR blocks"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = var.allowed_cidr_blocks
    }
  }

  # Restricted access rules (admin IPs only)
  dynamic "ingress" {
    for_each = var.restrict_public_access ? [1] : []
    content {
      description = "HTTP from admin IPs only"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = [for ip in var.admin_ip_addresses : "${ip}/32"]
    }
  }

  # VPC access rule (optional)
  dynamic "ingress" {
    for_each = var.enable_vpc_access ? [1] : []
    content {
      description = "HTTP from VPC"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = [aws_vpc.main.cidr_block]
    }
  }

  # HTTPS rules (if enabled)
  dynamic "ingress" {
    for_each = var.enable_https ? (var.restrict_public_access ? [] : [1]) : []
    content {
      description = "HTTPS from allowed CIDR blocks"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = var.allowed_cidr_blocks
    }
  }

  dynamic "ingress" {
    for_each = var.enable_https ? (var.restrict_public_access ? [1] : []) : []
    content {
      description = "HTTPS from admin IPs only"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = [for ip in var.admin_ip_addresses : "${ip}/32"]
    }
  }

  # Custom access rules
  dynamic "ingress" {
    for_each = var.custom_access_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = [ingress.value.cidr_block]
    }
  }

  # Egress to ECS tasks
  egress {
    description     = "To ECS tasks"
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-alb-sg"
    Type = "LoadBalancer"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.bucket
    prefix  = "alb-logs"
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-alb"
    Type = "LoadBalancer"
  })
}

# Target Group
resource "aws_lb_target_group" "main" {
  name        = "${var.project_name}-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-target-group"
    Type = "LoadBalancer"
  })
}

# HTTP Listener (Always created for basic access)
resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = var.enable_https ? "redirect" : "forward"

    dynamic "redirect" {
      for_each = var.enable_https ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    dynamic "forward" {
      for_each = var.enable_https ? [] : [1]
      content {
        target_group {
          arn = aws_lb_target_group.main.arn
        }
      }
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-http-listener"
    Type = "LoadBalancer"
  })
}

# HTTPS Listener (optional)
resource "aws_lb_listener" "https" {
  count = var.enable_https ? 1 : 0

  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-https-listener"
    Type = "LoadBalancer"
  })
}

# S3 Bucket for ALB Access Logs
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "${var.project_name}-alb-logs-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = merge(var.tags, {
    Name = "${var.project_name}-alb-logs"
    Type = "Logging"
  })
}

resource "aws_s3_bucket_versioning" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    id     = "delete_old_logs"
    status = "Enabled"

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

# ALB Access Logs Policy
data "aws_elb_service_account" "main" {}

resource "aws_s3_bucket_policy" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = data.aws_elb_service_account.main.arn
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/alb-logs/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/alb-logs/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.alb_logs.arn
      }
    ]
  })
}

# Random ID for unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}
