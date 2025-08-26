---
inclusion: always
---

# Technology Stack & Architecture Patterns

## Core Technologies

### Application Stack
- **Streamlit 1.28.1**: Main web framework
- **Python 3.x**: Primary language
- **Boto3 1.34.0+**: AWS SDK

### AI/ML Stack
- **Amazon Bedrock Nova Models**:
  - **Nova Micro**: Fast responses (1-3s)
  - **Nova Pro**: Detailed analysis (3-8s)
- **Bedrock Knowledge Base**: RAG capabilities
- **Prompt Caching**: Performance optimization

### AWS Infrastructure
- **ECS Fargate**: Serverless containers
- **ALB**: Multi-AZ load balancing
- **VPC**: Private subnets + NAT gateways
- **Secrets Manager**: Secure configuration
- **Terraform ~> 5.0**: Infrastructure automation

## Critical Architecture Patterns

### Parallel Processing (GitHub Original)
```python
# MUST use ThreadPoolExecutor for concurrent Nova models
with ThreadPoolExecutor(max_workers=2) as executor:
    micro_future = executor.submit(nova_micro_call)
    pro_future = executor.submit(nova_pro_call)
```

### Caching Strategy
- **Streamlit**: Use `@st.cache_resource` for AWS clients
- **Prompt Caching**: Enable for Nova models
- **Knowledge Base**: Cache search results

### Security Requirements
- **No Hardcoded Secrets**: Use AWS Secrets Manager only
- **Least Privilege IAM**: Task-specific permissions
- **Private Networking**: ECS in private subnets

### Performance Requirements
- **Response Time**: Sub-5 second target
- **Auto Scaling**: 1-10 ECS tasks based on CPU/memory
- **Health Checks**: Automatic failure recovery

## Development Commands

### Local Development
```bash
pip install -r config/requirements.txt
export AWS_DEFAULT_REGION=us-east-1
streamlit run src/chatbot_app.py
```

### Deployment
```bash
# One-command deployment
KNOWLEDGE_BASE_ID=your-kb-id ./scripts/deploy.sh

# Manual Terraform
cd terraform && terraform init && terraform apply
```

## Required Dependencies
```
streamlit==1.28.1
boto3==1.34.0
requests==2.31.0
langdetect==1.0.9
python-dotenv==1.0.0
pandas==2.1.4
numpy==1.24.3
```