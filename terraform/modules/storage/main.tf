# 스토리지 모듈 - S3, Secrets Manager

# Random ID for unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 Bucket for Code Storage
resource "aws_s3_bucket" "code" {
  bucket        = "${var.resource_prefix}-code-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-code-bucket"
    Type = "Storage"
    Tier = "Application"
    Service = "S3"
    Purpose = "CodeStorage"
  })
}

resource "aws_s3_bucket_versioning" "code" {
  bucket = aws_s3_bucket.code.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "code" {
  bucket = aws_s3_bucket.code.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "code" {
  bucket = aws_s3_bucket.code.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for ALB Access Logs
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "${var.resource_prefix}-alb-logs-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-alb-logs"
    Type = "Storage"
    Tier = "Logging"
    Service = "S3"
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
        Resource = "${aws_s3_bucket.alb_logs.arn}/alb-logs/AWSLogs/${var.account_id}/*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/alb-logs/AWSLogs/${var.account_id}/*"
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

# Upload the chatbot application code
resource "aws_s3_object" "chatbot_app" {
  bucket = aws_s3_bucket.code.bucket
  key    = "chatbot_app.py"
  source = var.chatbot_app_source_path
  etag   = filemd5(var.chatbot_app_source_path)

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-chatbot-application-code"
    Type = "Storage"
    Tier = "Application"
    Service = "S3"
    ContentType = "ApplicationCode"
  })
}

# Upload requirements.txt
resource "aws_s3_object" "requirements" {
  bucket = aws_s3_bucket.code.bucket
  key    = "requirements.txt"
  source = var.requirements_source_path
  etag   = filemd5(var.requirements_source_path)

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-python-requirements"
    Type = "Storage"
    Tier = "Application"
    Service = "S3"
    ContentType = "Dependencies"
  })
}

# Secrets Manager - Application Configuration
resource "aws_secretsmanager_secret" "app_config" {
  name                    = "${var.resource_prefix}/app-config"
  description             = "Application configuration for Global Dual Nova RAG Chatbot"
  recovery_window_in_days = 7

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-app-config"
    Type = "Security"
    Tier = "Application"
    Service = "SecretsManager"
    Purpose = "Configuration"
  })
}

resource "aws_secretsmanager_secret_version" "app_config" {
  secret_id = aws_secretsmanager_secret.app_config.id
  secret_string = jsonencode({
    knowledge_base_id = var.knowledge_base_id
    data_source_ids   = var.data_source_ids
    aws_region        = var.aws_region
    environment       = var.environment
  })
}

# Secrets Manager - Notion Token
resource "aws_secretsmanager_secret" "notion_token" {
  name                    = "${var.resource_prefix}/notion-token"
  description             = "Notion API token for Global Dual Nova RAG Chatbot"
  recovery_window_in_days = 7

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-notion-token"
    Type = "Security"
    Tier = "Application"
    Service = "SecretsManager"
    Purpose = "APIToken"
  })
}

resource "aws_secretsmanager_secret_version" "notion_token" {
  secret_id     = aws_secretsmanager_secret.notion_token.id
  secret_string = var.notion_token != "" ? var.notion_token : "placeholder-token"
}