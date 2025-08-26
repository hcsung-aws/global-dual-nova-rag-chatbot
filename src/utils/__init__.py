"""
Utils 모듈 - 유틸리티 함수

이 모듈은 공통으로 사용되는 유틸리티 함수들을 포함합니다:
- 게임 용어 단어장 관리
- 설정 관리
- 표준화된 에러 처리
- 표준화된 로깅 시스템
"""

from .glossary_manager import GlossaryManager, get_glossary_manager
from .config_manager import ConfigManager, get_config_manager
from .error_handler import (
    ErrorHandler, StandardError, ErrorSeverity, ErrorCategory, get_error_handler
)
from .logger import StandardLogger, get_logger, setup_logging_from_config
from .error_logging_utils import (
    handle_errors, log_performance, error_context, performance_context,
    log_aws_api_call, log_model_usage, ErrorLoggingMixin,
    safe_execute, get_user_friendly_error
)

__version__ = "1.0.0"
__author__ = "Global Dual Nova RAG Chatbot Team"

__all__ = [
    # 기존 유틸리티
    'GlossaryManager',
    'get_glossary_manager',
    'ConfigManager', 
    'get_config_manager',
    
    # 에러 처리
    'ErrorHandler',
    'StandardError',
    'ErrorSeverity',
    'ErrorCategory',
    'get_error_handler',
    
    # 로깅
    'StandardLogger',
    'get_logger',
    'setup_logging_from_config',
    
    # 통합 유틸리티
    'handle_errors',
    'log_performance',
    'error_context',
    'performance_context',
    'log_aws_api_call',
    'log_model_usage',
    'ErrorLoggingMixin',
    'safe_execute',
    'get_user_friendly_error'
]