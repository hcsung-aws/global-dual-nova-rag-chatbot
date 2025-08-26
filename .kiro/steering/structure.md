---
inclusion: always
---

# Project Structure & Code Organization

## Directory Structure

- `src/chatbot_app.py`: Main Streamlit application (monolithic design)
- `terraform/`: Infrastructure as Code (modular by AWS service)
- `config/`: Dependencies and game glossary (no secrets)
- `docs/`: Architecture, deployment, and cost analysis
- `scripts/`: Automation scripts with error handling

## Naming Conventions

### Code Style
- **Python**: Snake case (`user_language`, `generate_dual_answer`)
- **Functions**: Descriptive names (`create_translation_prompt_prefix`)
- **Logging**: Consistent prefixes (`log_info`, `log_error`)

### AWS Resources
- **Pattern**: `${var.project_name}-resource-type`
- **Suffixes**: `-vpc`, `-ecs`, `-alb`, `-sg`
- **Environment tags**: Required for cost allocation

### Files
- **Lowercase with hyphens**: Project directories
- **Descriptive names**: `chatbot_app.py`, `game_glossary.json`
- **Clear extensions**: `.tf`, `.py`, `.md`

## Code Organization Patterns

### Main Application Structure (chatbot_app.py)
```python
# 1. Imports and configuration
# 2. Streamlit page config
# 3. AWS client initialization (@st.cache_resource)
# 4. Game glossary functions (hardcoded for reliability)
# 5. Translation functions (Nova Pro with caching)
# 6. Knowledge Base search functions
# 7. Prompt generation (with caching optimization)
# 8. Streaming functions (Nova Micro/Pro)
# 9. Dual language response generation (GitHub original pattern)
# 10. Main Streamlit UI
```

### Terraform Organization
- **main.tf**: Core infrastructure (VPC, networking)
- **Service files**: `ecs.tf`, `alb.tf`, `s3.tf`
- **secrets.tf**: IAM roles and Secrets Manager
- **outputs.tf**: All important values exported

## Architecture Principles

### Application Design
- **Monolithic**: Single Streamlit app for simplicity
- **Embedded Config**: Game glossary hardcoded (no S3 dependency)
- **Caching**: Use `@st.cache_resource` for AWS clients

### Infrastructure Design
- **Modular Terraform**: Separate files by AWS service
- **Environment Support**: dev/staging/prod configurations
- **Security First**: Private subnets, Secrets Manager, IAM roles