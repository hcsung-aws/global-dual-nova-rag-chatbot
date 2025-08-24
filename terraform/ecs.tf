# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = "${var.project_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "${var.project_name}-container"
      image = var.container_image
      
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        },
        {
          name  = "DATA_BUCKET_NAME"
          value = aws_s3_bucket.code.bucket
        },
        {
          name  = "STREAMLIT_SERVER_ADDRESS"
          value = "0.0.0.0"
        },
        {
          name  = "STREAMLIT_SERVER_PORT"
          value = "8501"
        }
      ]
      
      secrets = [
        {
          name      = "NOTION_TOKEN_SECRET_ARN"
          valueFrom = aws_secretsmanager_secret.notion_token.arn
        },
        {
          name      = "APP_CONFIG_SECRET_ARN"
          valueFrom = aws_secretsmanager_secret.app_config.arn
        }
      ]
      
      command = [
        "bash",
        "-c",
        "apt-get update && apt-get install -y curl unzip && curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip awscliv2.zip && ./aws/install && pip install streamlit boto3 requests && mkdir -p /app && cd /app && aws s3 cp s3://${aws_s3_bucket.code.bucket}/chatbot_app.py app.py && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"
      ]
      
      logConfiguration = var.enable_logging ? {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs[0].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = var.project_name
        }
      } : null
      
      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-task-definition"
  }
}

# ECS Service
resource "aws_ecs_service" "main" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "${var.project_name}-container"
    container_port   = 8501
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 50
    
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  health_check_grace_period_seconds = 60

  depends_on = [
    aws_lb_listener.main,
    aws_iam_role_policy_attachment.ecs_task_execution,
    aws_iam_role_policy_attachment.ecs_task
  ]

  tags = {
    Name = "${var.project_name}-service"
  }
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "ecs" {
  count = var.enable_auto_scaling ? 1 : 0

  max_capacity       = var.ecs_max_capacity
  min_capacity       = var.ecs_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = {
    Name = "${var.project_name}-autoscaling-target"
  }
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "ecs_cpu" {
  count = var.enable_auto_scaling ? 1 : 0

  name               = "${var.project_name}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = var.auto_scaling_target_cpu
  }
}

# Auto Scaling Policy - Memory
resource "aws_appautoscaling_policy" "ecs_memory" {
  count = var.enable_auto_scaling ? 1 : 0

  name               = "${var.project_name}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = var.auto_scaling_target_memory
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  count = var.enable_logging ? 1 : 0

  name              = "/ecs/${var.project_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-log-group"
  }
}
