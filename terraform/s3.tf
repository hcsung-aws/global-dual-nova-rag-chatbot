# S3 Bucket for Code Storage
resource "aws_s3_bucket" "code" {
  bucket        = "${local.resource_prefix}-code-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-code-bucket"
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

# Upload the chatbot application code
resource "aws_s3_object" "chatbot_app" {
  bucket = aws_s3_bucket.code.bucket
  key    = "chatbot_app.py"
  source = "${path.module}/../src/chatbot_app.py"
  etag   = filemd5("${path.module}/../src/chatbot_app.py")

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-chatbot-application-code"
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
  source = "${path.module}/../config/requirements.txt"
  etag   = filemd5("${path.module}/../config/requirements.txt")

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-python-requirements"
    Type = "Storage"
    Tier = "Application"
    Service = "S3"
    ContentType = "Dependencies"
  })
}
