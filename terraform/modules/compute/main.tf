# 컴퓨팅 모듈 - ECS, ALB

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.resource_prefix}"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.common_tags, {
    Name    = "${var.resource_prefix}-log-group"
    Service = "CloudWatch"
    Tier    = "Logging"
  })
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.resource_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-cluster"
    Type = "Compute"
    Tier = "Application"
    Service = "ECS"
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = "${var.resource_prefix}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn           = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "${var.resource_prefix}-container"
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
          value = var.code_bucket_name
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
          valueFrom = var.notion_token_secret_arn
        },
        {
          name      = "APP_CONFIG_SECRET_ARN"
          valueFrom = var.app_config_secret_arn
        }
      ]
      
      command = [
        "bash",
        "-c",
        "echo 'Starting container setup...' && apt-get update -qq && apt-get install -y -qq curl unzip && echo 'Installing AWS CLI...' && curl -s 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip -q awscliv2.zip && ./aws/install && echo 'Downloading requirements...' && aws s3 cp s3://${var.code_bucket_name}/requirements.txt /tmp/requirements.txt && echo 'Installing Python packages...' && pip install -q -r /tmp/requirements.txt && echo 'Setting up application...' && mkdir -p /app && cd /app && aws s3 sync s3://${var.code_bucket_name}/src ./src && aws s3 sync s3://${var.code_bucket_name}/config ./config && export PYTHONPATH=/app:$PYTHONPATH && echo 'Starting Streamlit application...' && streamlit run src/chatbot_app.py --server.port=8501 --server.address=0.0.0.0"
      ]
      
      logConfiguration = var.enable_logging ? {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = var.resource_prefix
        }
      } : null
      
      essential = true
    }
  ])

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-task-definition"
    Type = "Compute"
    Tier = "Application"
    Service = "ECS"
  })
}

# ECS Service
resource "aws_ecs_service" "main" {
  name            = "${var.resource_prefix}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "${var.resource_prefix}-container"
    container_port   = 8501
  }

  health_check_grace_period_seconds = 600

  depends_on = [
    aws_lb_listener.main
  ]

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-service"
    Type = "Compute"
    Tier = "Application"
    Service = "ECS"
  })
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.resource_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false

  access_logs {
    bucket  = var.alb_logs_bucket_name
    prefix  = "alb-logs"
    enabled = true
  }

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-alb"
    Type = "LoadBalancer"
    Tier = "Network"
    Service = "ALB"
  })
}

# Target Group
resource "aws_lb_target_group" "main" {
  name        = "${var.resource_prefix}-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 90
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 60
    unhealthy_threshold = 10
  }

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-target-group"
    Type = "LoadBalancer"
    Tier = "Network"
    Service = "ALB"
  })
}

# HTTP Listener
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

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-http-listener"
    Type = "LoadBalancer"
    Tier = "Network"
    Service = "ALB"
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

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-https-listener"
    Type = "LoadBalancer"
    Tier = "Network"
    Service = "ALB"
  })
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "ecs" {
  count = var.enable_auto_scaling ? 1 : 0

  max_capacity       = var.ecs_max_capacity
  min_capacity       = var.ecs_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = merge(var.common_tags, {
    Name = "${var.resource_prefix}-autoscaling-target"
    Type = "Compute"
    Tier = "Application"
    Service = "AutoScaling"
  })
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "ecs_cpu" {
  count = var.enable_auto_scaling ? 1 : 0

  name               = "${var.resource_prefix}-cpu-scaling"
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

  name               = "${var.resource_prefix}-memory-scaling"
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