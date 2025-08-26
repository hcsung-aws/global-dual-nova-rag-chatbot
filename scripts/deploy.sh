#!/bin/bash

# Global Dual Nova RAG Chatbot Deployment Script
# This script automates the deployment of the chatbot infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="global-dual-nova-chatbot"
AWS_REGION="${AWS_REGION:-us-east-1}"
TERRAFORM_DIR="terraform"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check if Bedrock is available in the region
    if ! aws bedrock list-foundation-models --region $AWS_REGION &> /dev/null; then
        log_error "Amazon Bedrock is not available in region $AWS_REGION or access is not enabled."
        log_info "Please enable Bedrock access in the AWS console first."
        exit 1
    fi
    
    log_success "All prerequisites met!"
}

validate_knowledge_base() {
    log_info "Validating Knowledge Base configuration..."
    
    if [ -z "$KNOWLEDGE_BASE_ID" ]; then
        log_error "KNOWLEDGE_BASE_ID environment variable is not set."
        log_info "Please create a Knowledge Base in Amazon Bedrock and set the environment variable:"
        log_info "export KNOWLEDGE_BASE_ID=your-knowledge-base-id"
        exit 1
    fi
    
    # Validate Knowledge Base exists
    if ! aws bedrock-agent get-knowledge-base --knowledge-base-id "$KNOWLEDGE_BASE_ID" --region $AWS_REGION &> /dev/null; then
        log_error "Knowledge Base $KNOWLEDGE_BASE_ID not found in region $AWS_REGION"
        exit 1
    fi
    
    log_success "Knowledge Base validation passed!"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd $TERRAFORM_DIR
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    
    # Create terraform.tfvars if it doesn't exist
    if [ ! -f terraform.tfvars ]; then
        log_info "Creating terraform.tfvars file..."
        cat > terraform.tfvars << EOF
aws_region = "$AWS_REGION"
knowledge_base_id = "$KNOWLEDGE_BASE_ID"
data_source_ids = []
project_name = "$PROJECT_NAME"
environment = "production"
EOF
    fi
    
    # Plan deployment
    log_info "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    # Apply deployment
    log_info "Applying Terraform deployment..."
    terraform apply tfplan
    
    # Get outputs
    APPLICATION_URL=$(terraform output -raw application_url)
    S3_BUCKET=$(terraform output -raw s3_bucket_name)
    
    cd ..
    
    log_success "Infrastructure deployment completed!"
    log_info "Application URL: $APPLICATION_URL"
    log_info "S3 Bucket: $S3_BUCKET"
}

upload_application_code() {
    log_info "Uploading application code to S3..."
    
    # Get S3 bucket name from Terraform output
    cd $TERRAFORM_DIR
    S3_BUCKET=$(terraform output -raw s3_bucket_name)
    cd ..
    
    # Upload main application
    aws s3 cp src/chatbot_app.py s3://$S3_BUCKET/chatbot_app.py --region $AWS_REGION
    
    # Upload requirements
    aws s3 cp config/requirements.txt s3://$S3_BUCKET/requirements.txt --region $AWS_REGION
    
    log_success "Application code uploaded successfully!"
}

wait_for_deployment() {
    log_info "Waiting for ECS service to become stable..."
    
    cd $TERRAFORM_DIR
    CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
    SERVICE_NAME=$(terraform output -raw ecs_service_name)
    cd ..
    
    # Wait for service to stabilize
    aws ecs wait services-stable \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --region $AWS_REGION
    
    log_success "ECS service is now stable!"
}

test_deployment() {
    log_info "Testing deployment..."
    
    cd $TERRAFORM_DIR
    APPLICATION_URL=$(terraform output -raw application_url)
    cd ..
    
    # Wait a bit for the application to start
    sleep 30
    
    # Test if the application is responding
    if curl -f -s "$APPLICATION_URL" > /dev/null; then
        log_success "Application is responding successfully!"
        log_info "You can access your chatbot at: $APPLICATION_URL"
    else
        log_warning "Application might still be starting up. Please check manually at: $APPLICATION_URL"
    fi
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    
    cd $TERRAFORM_DIR
    terraform destroy -auto-approve
    cd ..
    
    log_info "Cleanup completed."
}

main() {
    log_info "Starting deployment of Global Dual Nova RAG Chatbot..."
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Run deployment steps
    check_prerequisites
    validate_knowledge_base
    deploy_infrastructure
    upload_application_code
    wait_for_deployment
    test_deployment
    
    log_success "Deployment completed successfully!"
    
    cd $TERRAFORM_DIR
    APPLICATION_URL=$(terraform output -raw application_url)
    cd ..
    
    echo ""
    echo "🎉 Your Global Dual Nova RAG Chatbot is now live!"
    echo "📱 Application URL: $APPLICATION_URL"
    echo ""
    echo "Next steps:"
    echo "1. Configure your Knowledge Base data sources"
    echo "2. Test the chatbot with sample queries"
    echo "3. Monitor the application in CloudWatch"
    echo "4. Set up alerts and monitoring"
    echo ""
    echo "For more information, see the documentation in the docs/ directory."
}

# Show usage if no Knowledge Base ID is provided
if [ -z "$KNOWLEDGE_BASE_ID" ]; then
    echo "Usage: KNOWLEDGE_BASE_ID=your-kb-id ./scripts/deploy.sh"
    echo ""
    echo "Before running this script:"
    echo "1. Create a Knowledge Base in Amazon Bedrock"
    echo "2. Note the Knowledge Base ID"
    echo "3. Set the environment variable: export KNOWLEDGE_BASE_ID=your-kb-id"
    echo "4. Run this script"
    exit 1
fi

# Run main function
main "$@"
