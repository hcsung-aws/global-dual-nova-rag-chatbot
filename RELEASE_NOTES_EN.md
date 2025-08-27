# Release Notes / 릴리즈 노트

> 📖 **한국어 버전**: [RELEASE_NOTES.md](RELEASE_NOTES.md)

## Version 0.1.0 (2025-08-28) - Initial Public Release

🎉 **The first public release of Global Dual Nova RAG Chatbot!**

### 📋 Key Features

- **Dual Language Support**: Korean (staff) + English (customer) responses
- **Dual Model Architecture**: Nova Micro (fast) + Nova Pro (detailed) parallel processing
- **RAG Integration**: Amazon Bedrock Knowledge Bases for contextual responses
- **Real-time Streaming**: GitHub-original parallel execution pattern
- **Game Character Recognition**: Built-in gaming glossary for character identification

### 🗓️ Development History

#### 2025-08-28
- **📁 Project Structure Documentation Update**
  - Updated README files to reflect actual project structure after refactoring
  - Reflected modularized src/ directory structure (config/, core/, services/, utils/)
  - Added modules/ and environments/ subdirectories to terraform/ structure
  - Added tests/, examples/, worklog/ directories

#### 2025-08-27
- **🧪 Test Code Improvements**
  - Improved test compatibility to match current code structure
  - Modified performance benchmarks and streaming handler tests

- **🔧 CloudWatch Error Resolution**
  - Resolved CloudWatch logging errors and improved application stability
  - Enhanced error handling and logging systems

- **🚀 AWS ECS Fargate Deployment Completed**
  - Completed production environment deployment and resolved issues
  - Secured infrastructure stability

- **⚡ Complete System Refactoring**
  - Optimized code structure and modularization
  - Improved performance and maintainability

#### 2025-08-26
- **🛡️ Security and Access Control Features Added**
  - Implemented comprehensive security settings and access control features
  - Integrated AWS Secrets Manager

#### 2025-08-25
- **📊 Cost Analysis Report Added**
  - Created detailed cost analysis and model comparison report
  - Added cost analysis section to README

#### 2025-08-24
- **📝 Documentation Improvements**
  - Set Korean as default README and separated English version
  - Improved project documentation structure

- **🚀 Initial Release**
  - Released first version of Global Dual Nova RAG Chatbot
  - Completed basic functionality implementation

### 🏗️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.9+
- **AI Models**: Amazon Bedrock Nova (Micro + Pro)
- **Infrastructure**: AWS ECS Fargate, Application Load Balancer
- **Storage**: Amazon S3, AWS Secrets Manager
- **Knowledge Base**: Amazon Bedrock Knowledge Bases
- **IaC**: Terraform

### 📈 Performance Metrics

- **Response Time**: Micro model 1-3s, Pro model 3-8s
- **Parallel Processing**: ~3-5s total
- **Concurrent Users**: 100+ (with auto-scaling)
- **Availability**: 99.9% (multi-AZ deployment)

### 💰 Cost Efficiency

- **Nova Micro + Pro**: $46.34/month (medium complexity scenario)
- **vs Claude 3.5 Sonnet**: 77% cost reduction
- **Prompt Caching**: Additional 20-40% savings possible

### 🔒 Security Features

- Sensitive information management via AWS Secrets Manager
- VPC private subnet configuration
- IAM least privilege principle applied
- HTTPS/SSL encryption
- Access control and IP restriction features

### 🚀 Deployment

```bash
git clone https://github.com/hcsung-aws/global-dual-nova-rag-chatbot.git
cd global-dual-nova-rag-chatbot
cd terraform
terraform init
terraform apply
```

### 🤝 Contributors

- **Hyunchang Sung** (@hcsung-aws) - Project Lead and Full Development

### 📄 License

MIT License

---

**See you in the next version (0.2.0)! 🚀**
