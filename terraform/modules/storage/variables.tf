# 스토리지 모듈 변수

variable "resource_prefix" {
  description = "Resource naming prefix"
  type        = string
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "knowledge_base_id" {
  description = "Amazon Bedrock Knowledge Base ID"
  type        = string
}

variable "data_source_ids" {
  description = "List of data source IDs for the Knowledge Base"
  type        = list(string)
}

variable "notion_token" {
  description = "Notion API token"
  type        = string
  sensitive   = true
}

variable "chatbot_app_source_path" {
  description = "Path to the chatbot application source file"
  type        = string
}

variable "requirements_source_path" {
  description = "Path to the requirements.txt file"
  type        = string
}