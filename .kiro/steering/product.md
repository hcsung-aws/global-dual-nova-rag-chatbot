---
inclusion: always
---

# Product Conventions

## Global Dual Nova RAG Chatbot

Enterprise-grade multilingual chatbot with dual-language support (Korean + English), RAG capabilities, and parallel processing.

### Core Product Principles

- **Dual Language Output**: Always provide Korean responses for staff + English for customers
- **Parallel Processing**: Use ThreadPoolExecutor with Nova Micro (fast) + Nova Pro (detailed) simultaneously
- **Gaming Focus**: Specialized gaming terminology and character recognition required
- **Real-time Streaming**: Buffer-based natural conversation flow with typing effects
- **Cost Optimization**: 77% cost reduction target vs Claude 3.5 Sonnet

### Key Features to Maintain

- **Language Detection**: Automatic Korean/English detection with appropriate formatting
- **Game Glossary**: Built-in gaming terminology for accurate character identification
- **Prompt Caching**: Nova model optimization for performance and cost
- **Enterprise Security**: IAM roles, Secrets Manager, private subnets

### Target User Experience

- **Korean Staff**: Internal verification and processing responses
- **English Customers**: Dual-language customer service responses
- **Performance**: Sub-5 second response times required