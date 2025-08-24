# Global Dual Nova RAG Chatbot

🌍 **Enterprise-grade multilingual customer service chatbot** powered by Amazon Bedrock Nova models with dual-language support and RAG (Retrieval-Augmented Generation) capabilities.

> 📖 **한국어 버전**: [README.md](README.md)

## 🚀 Features

### Core Capabilities
- **Dual Language Support**: Korean (staff) + English (customer) responses
- **Dual Model Architecture**: Nova Micro (fast) + Nova Pro (detailed) parallel processing
- **RAG Integration**: Amazon Bedrock Knowledge Bases for contextual responses
- **Real-time Streaming**: GitHub-original parallel execution pattern
- **Game Character Recognition**: Built-in gaming glossary for character identification

### Technical Highlights
- **True Parallel Processing**: ThreadPoolExecutor-based concurrent model execution
- **Buffer-based Streaming**: Real-time response display with natural typing effects
- **Prompt Caching**: Nova model caching for improved performance
- **Auto-scaling Infrastructure**: AWS ECS Fargate with Application Load Balancer
- **Secure Configuration**: AWS Secrets Manager integration

## 📋 Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0
- AWS CLI configured
- Amazon Bedrock access enabled
- Knowledge Base created in Amazon Bedrock

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │    │   Load Balancer  │    │   ECS Fargate   │
│   Load Balancer │◄──►│                  │◄──►│   Container     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐             │
                       │   Secrets        │◄────────────┘
                       │   Manager        │
                       └──────────────────┘
                                │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Amazon        │    │   Amazon         │    │   Amazon        │
│   Bedrock       │◄──►│   Bedrock        │◄──►│   S3 Bucket     │
│   Nova Models   │    │   Knowledge Base │    │   (Code Storage)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/hcsung-aws/global-dual-nova-rag-chatbot.git
cd global-dual-nova-rag-chatbot
```

### 2. Configure AWS Credentials
```bash
aws configure
```

### 3. Create Knowledge Base
1. Go to Amazon Bedrock Console
2. Create a new Knowledge Base
3. Note the Knowledge Base ID
4. Update `terraform/variables.tf` with your Knowledge Base ID

### 4. Deploy Infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 5. Access Application
After deployment, Terraform will output the Application Load Balancer URL.

## 📁 Project Structure

```
global-dual-nova-rag-chatbot/
├── src/
│   └── chatbot_app.py          # Main Streamlit application
├── terraform/
│   ├── main.tf                 # Main infrastructure configuration
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Output values
│   ├── ecs.tf                  # ECS service configuration
│   ├── alb.tf                  # Application Load Balancer
│   ├── secrets.tf              # Secrets Manager configuration
│   └── s3.tf                   # S3 bucket for code storage
├── config/
│   ├── requirements.txt        # Python dependencies
│   └── game_glossary.json      # Gaming character glossary
├── docs/
│   ├── ARCHITECTURE.md         # Detailed architecture documentation
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── API.md                  # API documentation
├── assets/
│   └── architecture-diagram.txt # Architecture diagram
├── scripts/
│   ├── deploy.sh               # Deployment script
│   └── cleanup.sh              # Cleanup script
└── README.md                   # Korean version (main)
```

## 🔧 Configuration

### Environment Variables
The application uses AWS Secrets Manager for configuration:

- `NOTION_TOKEN_SECRET_ARN`: Notion API token (if using Notion integration)
- `APP_CONFIG_SECRET_ARN`: Application configuration including Knowledge Base ID

### Knowledge Base Configuration
Update the Knowledge Base ID in your secrets:
```json
{
  "knowledge_base_id": "your-knowledge-base-id-here",
  "data_source_ids": ["your-data-source-id-here"]
}
```

## 🎯 Usage

### For Korean Users
- Ask questions in Korean
- Receive responses using GitHub-original parallel processing (Micro + Pro)

### For English Users
- Ask questions in English
- Receive dual-language responses:
  1. Korean response (for staff verification)
  2. English response (for customer)

### Language Detection
The system automatically detects input language and responds accordingly.

## 🔄 Dual Model Processing

### GitHub Original Pattern
```python
# Pro model runs in background
with ThreadPoolExecutor(max_workers=2) as executor:
    future_pro = executor.submit(collect_pro_stream)
    
    # Micro model streams in real-time
    for chunk in stream_nova_model('nova-micro', prompt):
        display_chunk(chunk)
    
    # Pro results displayed from buffer
    display_pro_results(future_pro.result())
```

### Performance Benefits
- **Faster Response Time**: Micro model provides immediate feedback
- **Detailed Analysis**: Pro model adds comprehensive insights
- **Parallel Execution**: Both models run simultaneously
- **Natural Flow**: Buffer-based streaming creates smooth user experience

## 📊 Monitoring

### CloudWatch Metrics
- ECS service health
- Application Load Balancer metrics
- Bedrock API usage
- Response times

### Logging
- Application logs in CloudWatch
- ECS task logs
- Load balancer access logs

## 🔒 Security

### Best Practices Implemented
- **Secrets Management**: All sensitive data in AWS Secrets Manager
- **Network Security**: VPC with private subnets
- **IAM Roles**: Least privilege access
- **HTTPS**: SSL/TLS encryption
- **Container Security**: Fargate managed containers

## 🚀 Scaling

### Auto Scaling
- ECS service auto-scaling based on CPU/memory
- Application Load Balancer distributes traffic
- Fargate automatically manages infrastructure

### Cost Optimization
- Fargate Spot instances (optional)
- Bedrock on-demand pricing
- S3 lifecycle policies

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r config/requirements.txt

# Set environment variables
export AWS_DEFAULT_REGION=us-east-1
export DATA_BUCKET_NAME=your-bucket-name

# Run locally
streamlit run src/chatbot_app.py
```

### Testing
```bash
# Test Bedrock connectivity
python scripts/test_bedrock.py

# Test Knowledge Base
python scripts/test_knowledge_base.py
```

## 📈 Performance Metrics

### Response Times (Typical)
- **Micro Model**: 1-3 seconds
- **Pro Model**: 3-8 seconds
- **Parallel Processing**: ~3-5 seconds total
- **Knowledge Base Query**: 0.5-2 seconds

### Throughput
- **Concurrent Users**: 100+ (with auto-scaling)
- **Requests per Second**: 50+ per container
- **Availability**: 99.9% (multi-AZ deployment)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues
- **Bedrock Access**: Ensure Bedrock is enabled in your region
- **Knowledge Base**: Verify Knowledge Base ID is correct
- **Permissions**: Check IAM roles have necessary permissions

### Getting Help
- Create an issue in this repository
- Check the [docs/](docs/) directory for detailed guides
- Review CloudWatch logs for debugging

## 🏆 Acknowledgments

- Based on the original dual model pattern from [Hyunsoo0128/Dual_Model_ChatBot](https://github.com/Hyunsoo0128/Dual_Model_ChatBot)
- In-game chat translation and glossary features are implemented with reference to [KakaoGames' Amazon Bedrock use case](https://aws.amazon.com/ko/blogs/tech/kakaogames-amazon-bedrock-in-game-chat-translation/)
- Powered by Amazon Bedrock Nova models
- Built with Streamlit and AWS services

---

**Made with ❤️ for global customer service excellence**
