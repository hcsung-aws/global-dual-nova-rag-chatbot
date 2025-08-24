# Architecture Documentation

## Overview

The Global Dual Nova RAG Chatbot is built on a modern, scalable architecture using AWS services. This document provides detailed information about the system architecture, components, and data flow.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                Application Load Balancer                        │
│                    (Multi-AZ)                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                           │
│  ┌─────────────────┬───────────────────┬─────────────────────┐  │
│  │  Public Subnet  │   Public Subnet   │                     │  │
│  │  (10.0.1.0/24)  │   (10.0.2.0/24)   │                     │  │
│  │                 │                   │                     │  │
│  │  ┌─────────────┐│  ┌─────────────┐  │                     │  │
│  │  │ NAT Gateway ││  │ NAT Gateway │  │                     │  │
│  │  └─────────────┘│  └─────────────┘  │                     │  │
│  └─────────────────┼───────────────────┼─────────────────────┘  │
│  ┌─────────────────▼───────────────────▼─────────────────────┐  │
│  │               Private Subnets                             │  │
│  │         (10.0.10.0/24, 10.0.20.0/24)                     │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              ECS Fargate Tasks                      │  │  │
│  │  │          (Auto Scaling Group)                       │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │  │
│  │  │  │ Streamlit   │  │ Streamlit   │  │ Streamlit   │  │  │  │
│  │  │  │ Container   │  │ Container   │  │ Container   │  │  │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   AWS Services                                  │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Amazon    │  │   Amazon    │  │     S3      │             │
│  │   Bedrock   │  │   Bedrock   │  │   Bucket    │             │
│  │ Nova Models │  │ Knowledge   │  │ (Code Store)│             │
│  │             │  │    Base     │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Secrets    │  │ CloudWatch  │  │    IAM      │             │
│  │  Manager    │  │    Logs     │  │   Roles     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Application Load Balancer (ALB)
- **Purpose**: Distributes incoming traffic across multiple ECS tasks
- **Features**:
  - Health checks for ECS targets
  - SSL/TLS termination (optional)
  - Access logging to S3
  - Multi-AZ deployment for high availability

### 2. Amazon ECS Fargate
- **Purpose**: Serverless container orchestration
- **Configuration**:
  - CPU: 512 units (0.5 vCPU)
  - Memory: 1024 MB (1 GB)
  - Auto-scaling based on CPU and memory utilization
  - Rolling deployments with circuit breaker

### 3. VPC and Networking
- **VPC CIDR**: 10.0.0.0/16
- **Public Subnets**: 10.0.1.0/24, 10.0.2.0/24 (ALB)
- **Private Subnets**: 10.0.10.0/24, 10.0.20.0/24 (ECS tasks)
- **NAT Gateways**: Provide internet access for private subnets
- **Security Groups**: Restrict traffic between components

### 4. Amazon Bedrock Integration
- **Nova Micro Model**: Fast responses (1-3 seconds)
- **Nova Pro Model**: Detailed analysis (3-8 seconds)
- **Knowledge Base**: RAG capabilities for contextual responses
- **Parallel Processing**: Both models run simultaneously

### 5. Storage and Configuration
- **S3 Bucket**: Stores application code and static assets
- **Secrets Manager**: Secure storage for API keys and configuration
- **CloudWatch Logs**: Centralized logging and monitoring

## Data Flow

### 1. User Request Flow
```
User → ALB → ECS Task → Streamlit App → Language Detection
```

### 2. Korean User Flow
```
Korean Query → Knowledge Base → Nova Micro + Nova Pro (Parallel) → Korean Response
```

### 3. English User Flow
```
English Query → Knowledge Base → 
├─ Korean Response (Nova Micro + Pro Parallel)
└─ English Response (Nova Micro + Pro Parallel)
```

### 4. Parallel Processing Pattern
```
ThreadPoolExecutor:
├─ Background: Nova Pro Model (Buffer Collection)
└─ Foreground: Nova Micro Model (Real-time Streaming)
```

## Security Architecture

### 1. Network Security
- **Private Subnets**: ECS tasks run in private subnets
- **Security Groups**: Least privilege access rules
- **NAT Gateways**: Controlled internet access
- **VPC Flow Logs**: Network traffic monitoring

### 2. Application Security
- **IAM Roles**: Task-specific permissions
- **Secrets Manager**: Encrypted credential storage
- **HTTPS**: SSL/TLS encryption (optional)
- **Container Security**: Fargate managed security

### 3. Data Security
- **Encryption at Rest**: S3 and Secrets Manager
- **Encryption in Transit**: HTTPS/TLS
- **Access Logging**: ALB and CloudWatch logs
- **Audit Trail**: CloudTrail integration

## Scalability and Performance

### 1. Auto Scaling
- **Target Tracking**: CPU and memory-based scaling
- **Scale Out**: 1-10 tasks (configurable)
- **Scale In**: Gradual reduction during low traffic
- **Health Checks**: Automatic unhealthy task replacement

### 2. Performance Optimization
- **Parallel Processing**: Dual model execution
- **Prompt Caching**: Nova model caching for repeated queries
- **Connection Pooling**: Efficient resource utilization
- **CDN Ready**: Static asset optimization (future)

### 3. Monitoring and Alerting
- **CloudWatch Metrics**: ECS, ALB, and custom metrics
- **Log Aggregation**: Centralized logging
- **Health Dashboards**: Real-time system status
- **Automated Alerts**: Threshold-based notifications

## Disaster Recovery

### 1. High Availability
- **Multi-AZ Deployment**: ALB and NAT Gateways
- **Auto Scaling**: Automatic failure recovery
- **Health Checks**: Proactive failure detection
- **Rolling Deployments**: Zero-downtime updates

### 2. Backup and Recovery
- **S3 Versioning**: Code and configuration backup
- **Secrets Backup**: Automated secret rotation
- **Infrastructure as Code**: Terraform state management
- **Point-in-Time Recovery**: CloudWatch log retention

## Cost Optimization

### 1. Resource Optimization
- **Fargate Pricing**: Pay-per-use compute
- **Auto Scaling**: Right-sizing based on demand
- **Spot Instances**: Cost reduction (optional)
- **Reserved Capacity**: Long-term cost savings

### 2. Monitoring and Control
- **Cost Allocation Tags**: Resource-level cost tracking
- **Budget Alerts**: Spending threshold notifications
- **Usage Analytics**: Resource utilization insights
- **Lifecycle Policies**: Automated cleanup

## Future Enhancements

### 1. Performance Improvements
- **CDN Integration**: CloudFront for static assets
- **Caching Layer**: ElastiCache for frequent queries
- **Database Integration**: RDS for user sessions
- **API Gateway**: Rate limiting and throttling

### 2. Feature Additions
- **Multi-Region**: Global deployment
- **A/B Testing**: Feature flag management
- **Analytics**: User behavior tracking
- **Mobile Support**: Responsive design optimization

### 3. Security Enhancements
- **WAF Integration**: Web application firewall
- **DDoS Protection**: Shield Advanced
- **Compliance**: SOC 2, GDPR readiness
- **Zero Trust**: Enhanced access controls
