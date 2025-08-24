#!/bin/bash

# Global Dual Nova RAG Chatbot Cleanup Script
# This script removes all deployed resources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
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

confirm_cleanup() {
    echo ""
    log_warning "This will destroy ALL resources created by this project!"
    log_warning "This action cannot be undone."
    echo ""
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log_info "Cleanup cancelled."
        exit 0
    fi
}

cleanup_terraform() {
    log_info "Destroying Terraform-managed resources..."
    
    cd $TERRAFORM_DIR
    
    if [ ! -f terraform.tfstate ]; then
        log_warning "No Terraform state found. Nothing to destroy."
        cd ..
        return
    fi
    
    # Plan destroy
    terraform plan -destroy -out=destroy.tfplan
    
    # Apply destroy
    terraform apply destroy.tfplan
    
    # Clean up plan files
    rm -f tfplan destroy.tfplan
    
    cd ..
    
    log_success "Terraform resources destroyed successfully!"
}

cleanup_local_files() {
    log_info "Cleaning up local files..."
    
    # Remove Terraform state files (optional)
    read -p "Remove Terraform state files? (y/N): " remove_state
    if [ "$remove_state" = "y" ] || [ "$remove_state" = "Y" ]; then
        rm -f $TERRAFORM_DIR/terraform.tfstate*
        rm -f $TERRAFORM_DIR/.terraform.lock.hcl
        rm -rf $TERRAFORM_DIR/.terraform/
        log_info "Terraform state files removed."
    fi
    
    log_success "Local cleanup completed!"
}

verify_cleanup() {
    log_info "Verifying cleanup..."
    
    cd $TERRAFORM_DIR
    
    # Check if any resources remain
    if terraform show 2>/dev/null | grep -q "resource"; then
        log_warning "Some resources may still exist. Please check manually."
    else
        log_success "All resources have been cleaned up successfully!"
    fi
    
    cd ..
}

main() {
    log_info "Starting cleanup of Global Dual Nova RAG Chatbot resources..."
    
    confirm_cleanup
    cleanup_terraform
    cleanup_local_files
    verify_cleanup
    
    log_success "Cleanup completed!"
    
    echo ""
    echo "🧹 All resources have been cleaned up."
    echo ""
    echo "Note: The following items are NOT automatically removed:"
    echo "- Amazon Bedrock Knowledge Base (manual deletion required)"
    echo "- CloudWatch log data (subject to retention policy)"
    echo "- Any custom data sources you created"
    echo ""
    echo "Please review these items manually if needed."
}

# Run main function
main "$@"
