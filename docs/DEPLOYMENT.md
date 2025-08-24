# Deployment Guide

This guide provides step-by-step instructions for deploying the Global Dual Nova RAG Chatbot.

## Prerequisites

### 1. AWS Account Setup
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Amazon Bedrock access enabled in your region

### 2. Required Tools
- **Terraform** >= 1.0
- **AWS CLI** >= 2.0
- **Git** for cloning the repository
- **Bash** shell (Linux/macOS/WSL)

### 3. Permissions Required
Your AWS user/role needs the following permissions:
- ECS full access
- VPC management
- IAM role creation
- S3 bucket management
- Secrets Manager access
- Application Load Balancer management
- CloudWatch Logs access
- Bedrock access

## Step-by-Step Deployment

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/global-dual-nova-rag-chatbot.git
cd global-dual-nova-rag-chatbot
```

### Step 2: Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and preferred region
```

### Step 3: Enable Amazon Bedrock
1. Go to the AWS Console
2. Navigate to Amazon Bedrock
3. Enable access to Nova models (nova-micro-v1:0 and nova-pro-v1:0)
4. Request access if needed (may take a few minutes)

### Step 4: Create Knowledge Base
1. In the Bedrock console, go to "Knowledge bases"
2. Click "Create knowledge base"
3. Follow the wizard to create your knowledge base
4. Note the Knowledge Base ID (you'll need this for deployment)
5. Add data sources to your knowledge base

### Step 5: Set Environment Variables
```bash
export KNOWLEDGE_BASE_ID="your-knowledge-base-id-here"
export AWS_REGION="us-east-1"  # or your preferred region
```

### Step 6: Deploy Infrastructure
```bash
# Option 1: Use the automated deployment script
KNOWLEDGE_BASE_ID=your-kb-id ./scripts/deploy.sh

# Option 2: Manual Terraform deployment
cd terraform
terraform init
terraform plan -var="knowledge_base_id=your-kb-id"
terraform apply
```

### Step 7: Verify Deployment
After deployment completes, you'll see output similar to:
```
Outputs:
application_url = "http://your-alb-dns-name.us-east-1.elb.amazonaws.com"
```

Visit the URL to access your chatbot.

## Configuration Options

### Terraform Variables
You can customize the deployment by modifying `terraform/terraform.tfvars`:

```hcl
# Basic Configuration
aws_region = "us-east-1"
knowledge_base_id = "your-knowledge-base-id"
project_name = "my-chatbot"
environment = "production"

# Scaling Configuration
ecs_desired_count = 2
ecs_min_capacity = 1
ecs_max_capacity = 10
enable_auto_scaling = true

# Resource Configuration
ecs_cpu = 1024
ecs_memory = 2048

# Security Configuration
enable_https = true
ssl_certificate_arn = "arn:aws:acm:region:account:certificate/cert-id"

# Monitoring Configuration
enable_logging = true
log_retention_days = 14
```

### Environment-Specific Deployments
For multiple environments (dev, staging, prod):

```bash
# Development
terraform workspace new dev
terraform apply -var-file="environments/dev.tfvars"

# Production
terraform workspace new prod
terraform apply -var-file="environments/prod.tfvars"
```

## Post-Deployment Configuration

### 1. Update Secrets Manager
If you need to update configuration after deployment:

```bash
# Update Knowledge Base configuration
aws secretsmanager update-secret \
  --secret-id "global-dual-nova-chatbot/app-config" \
  --secret-string '{"knowledge_base_id":"new-kb-id","data_source_ids":["ds-1","ds-2"]}'

# Update Notion token (if using)
aws secretsmanager update-secret \
  --secret-id "global-dual-nova-chatbot/notion-token" \
  --secret-string "your-notion-token"
```

### 2. Force ECS Deployment
After updating secrets or code:

```bash
aws ecs update-service \
  --cluster global-dual-nova-chatbot-cluster \
  --service global-dual-nova-chatbot-service \
  --force-new-deployment
```

### 3. Monitor Deployment
```bash
# Check ECS service status
aws ecs describe-services \
  --cluster global-dual-nova-chatbot-cluster \
  --services global-dual-nova-chatbot-service

# Check CloudWatch logs
aws logs tail /ecs/global-dual-nova-chatbot --follow
```

## Troubleshooting

### Common Issues

#### 1. Bedrock Access Denied
**Error**: `AccessDeniedException` when calling Bedrock
**Solution**: 
- Ensure Bedrock access is enabled in your region
- Check IAM permissions for Bedrock actions
- Verify Nova models are available in your region

#### 2. Knowledge Base Not Found
**Error**: Knowledge Base ID not found
**Solution**:
- Verify the Knowledge Base ID is correct
- Ensure it's in the same region as your deployment
- Check that the Knowledge Base is in "Active" status

#### 3. ECS Task Startup Issues
**Error**: Tasks failing to start or health checks failing
**Solution**:
- Check CloudWatch logs for detailed error messages
- Verify S3 bucket permissions
- Ensure Secrets Manager access is configured

#### 4. Application Load Balancer 502/503 Errors
**Error**: Bad Gateway or Service Unavailable
**Solution**:
- Check ECS task health status
- Verify security group rules allow ALB → ECS communication
- Check target group health checks

### Debugging Commands

```bash
# Check ECS task logs
aws logs get-log-events \
  --log-group-name "/ecs/global-dual-nova-chatbot" \
  --log-stream-name "your-log-stream"

# Check ECS task status
aws ecs list-tasks \
  --cluster global-dual-nova-chatbot-cluster \
  --service-name global-dual-nova-chatbot-service

# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn "your-target-group-arn"

# Test Bedrock connectivity
aws bedrock list-foundation-models --region us-east-1

# Test Knowledge Base
aws bedrock-agent get-knowledge-base \
  --knowledge-base-id "your-kb-id"
```

## Scaling and Performance

### Auto Scaling Configuration
The deployment includes auto-scaling based on CPU and memory:

```hcl
# In terraform/variables.tf
auto_scaling_target_cpu = 70     # Scale out at 70% CPU
auto_scaling_target_memory = 80  # Scale out at 80% memory
ecs_min_capacity = 1             # Minimum tasks
ecs_max_capacity = 10            # Maximum tasks
```

### Performance Tuning
1. **Increase CPU/Memory**: For better response times
2. **Adjust Auto Scaling**: Based on your traffic patterns
3. **Enable CloudFront**: For static asset caching (future enhancement)
4. **Optimize Knowledge Base**: Ensure data sources are well-structured

## Security Best Practices

### 1. Network Security
- ECS tasks run in private subnets
- Security groups follow least privilege principle
- ALB access logs enabled

### 2. Application Security
- Secrets stored in AWS Secrets Manager
- IAM roles with minimal required permissions
- HTTPS enabled (when SSL certificate provided)

### 3. Monitoring and Alerting
- CloudWatch logs for all components
- ECS service monitoring
- ALB access and error logs

## Cost Optimization

### 1. Resource Right-Sizing
- Monitor CPU/memory utilization
- Adjust ECS task size based on actual usage
- Use auto-scaling to handle traffic spikes

### 2. Cost Monitoring
- Enable AWS Cost Explorer
- Set up billing alerts
- Use resource tagging for cost allocation

### 3. Cleanup Unused Resources
```bash
# Remove the entire deployment
./scripts/cleanup.sh

# Or use Terraform directly
cd terraform
terraform destroy
```

## Backup and Recovery

### 1. Infrastructure Backup
- Terraform state is your infrastructure backup
- Store state in S3 with versioning (recommended)
- Regular state file backups

### 2. Application Backup
- Application code is stored in S3
- Secrets are backed up in Secrets Manager
- Knowledge Base data should be backed up separately

### 3. Disaster Recovery
- Multi-AZ deployment provides high availability
- Auto-scaling handles instance failures
- ALB health checks ensure traffic routing to healthy instances

## Next Steps

After successful deployment:

1. **Configure Knowledge Base**: Add your data sources
2. **Test Functionality**: Try both Korean and English queries
3. **Set Up Monitoring**: Create CloudWatch dashboards
4. **Configure Alerts**: Set up notifications for issues
5. **Performance Testing**: Load test your deployment
6. **Security Review**: Conduct security assessment
7. **Documentation**: Document your specific configuration

For additional help, refer to:
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- AWS Documentation for individual services
