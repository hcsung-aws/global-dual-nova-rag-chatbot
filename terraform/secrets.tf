# Secrets Manager - Application Configuration
resource "aws_secretsmanager_secret" "app_config" {
  name                    = "${local.resource_prefix}/app-config"
  description             = "Application configuration for Global Dual Nova RAG Chatbot"
  recovery_window_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-app-config"
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
  name                    = "${local.resource_prefix}/notion-token"
  description             = "Notion API token for Global Dual Nova RAG Chatbot"
  recovery_window_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-notion-token"
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

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.resource_prefix}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-ecs-task-execution-role"
    Type = "Security"
    Tier = "Application"
    Service = "IAM"
    Purpose = "ECSTaskExecution"
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for Secrets Manager access
resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "${local.resource_prefix}-ecs-task-execution-secrets"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.app_config.arn,
          aws_secretsmanager_secret.notion_token.arn
        ]
      }
    ]
  })
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task" {
  name = "${local.resource_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-ecs-task-role"
    Type = "Security"
    Tier = "Application"
    Service = "IAM"
    Purpose = "ECSTask"
  })
}

# IAM Policy for ECS Task
resource "aws_iam_role_policy" "ecs_task" {
  name = "${local.resource_prefix}-ecs-task-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:RetrieveAndGenerate",
          "bedrock:Retrieve"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.code.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.code.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.app_config.arn,
          aws_secretsmanager_secret.notion_token.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
