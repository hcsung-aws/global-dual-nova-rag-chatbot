"""
표준화된 에러 처리 시스템

이 모듈은 애플리케이션 전반에 걸쳐 일관된 에러 처리와 
사용자 친화적인 에러 메시지를 제공합니다.
"""

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError


class ErrorSeverity(Enum):
    """에러 심각도 레벨"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """에러 카테고리"""
    AWS_SERVICE = "AWS_SERVICE"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    CONFIGURATION = "CONFIGURATION"
    NETWORK = "NETWORK"
    VALIDATION = "VALIDATION"
    SYSTEM = "SYSTEM"


@dataclass
class StandardError:
    """표준화된 에러 데이터 구조"""
    error_code: str
    message: str
    user_message: str  # 사용자 친화적 메시지
    category: ErrorCategory
    severity: ErrorSeverity
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    original_exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    
    def __post_init__(self):
        """초기화 후 처리"""
        if self.original_exception and not self.stack_trace:
            self.stack_trace = traceback.format_exc()


class ErrorHandler:
    """표준화된 에러 처리기"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        에러 핸들러 초기화
        
        Args:
            logger: 로깅에 사용할 로거 인스턴스
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # 사용자 친화적 메시지 매핑 (한국어/영어)
        self._user_messages = {
            "ko": {
                "AWS_CONNECTION_ERROR": "AWS 서비스 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "AWS_CREDENTIALS_ERROR": "AWS 인증 정보에 문제가 있습니다. 관리자에게 문의해주세요.",
                "AWS_PERMISSION_ERROR": "AWS 서비스 접근 권한이 부족합니다. 관리자에게 문의해주세요.",
                "AWS_THROTTLING_ERROR": "요청이 너무 많아 일시적으로 제한되었습니다. 잠시 후 다시 시도해주세요.",
                "MODEL_INFERENCE_ERROR": "AI 모델 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                "MODEL_TIMEOUT_ERROR": "AI 모델 응답 시간이 초과되었습니다. 질문을 간단히 하거나 다시 시도해주세요.",
                "CONFIG_MISSING_ERROR": "필수 설정이 누락되었습니다. 관리자에게 문의해주세요.",
                "CONFIG_INVALID_ERROR": "설정 값이 올바르지 않습니다. 관리자에게 문의해주세요.",
                "NETWORK_ERROR": "네트워크 연결에 문제가 발생했습니다. 인터넷 연결을 확인해주세요.",
                "VALIDATION_ERROR": "입력 값이 올바르지 않습니다. 다시 확인해주세요.",
                "SYSTEM_ERROR": "시스템 오류가 발생했습니다. 관리자에게 문의해주세요.",
                "UNKNOWN_ERROR": "알 수 없는 오류가 발생했습니다. 관리자에게 문의해주세요."
            },
            "en": {
                "AWS_CONNECTION_ERROR": "There was a problem connecting to AWS services. Please try again later.",
                "AWS_CREDENTIALS_ERROR": "There is an issue with AWS credentials. Please contact the administrator.",
                "AWS_PERMISSION_ERROR": "Insufficient permissions to access AWS services. Please contact the administrator.",
                "AWS_THROTTLING_ERROR": "Too many requests. Please wait a moment and try again.",
                "MODEL_INFERENCE_ERROR": "An error occurred while processing with the AI model. Please try again.",
                "MODEL_TIMEOUT_ERROR": "AI model response timed out. Please simplify your question or try again.",
                "CONFIG_MISSING_ERROR": "Required configuration is missing. Please contact the administrator.",
                "CONFIG_INVALID_ERROR": "Configuration values are invalid. Please contact the administrator.",
                "NETWORK_ERROR": "Network connection problem occurred. Please check your internet connection.",
                "VALIDATION_ERROR": "Input values are invalid. Please check and try again.",
                "SYSTEM_ERROR": "A system error occurred. Please contact the administrator.",
                "UNKNOWN_ERROR": "An unknown error occurred. Please contact the administrator."
            }
        }
    
    def handle_aws_error(self, error: Exception, context: Dict[str, Any] = None) -> StandardError:
        """
        AWS 관련 에러 처리
        
        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        context = context or {}
        
        if isinstance(error, NoCredentialsError):
            return StandardError(
                error_code="AWS_CREDENTIALS_ERROR",
                message=f"AWS credentials not found: {str(error)}",
                user_message=self._get_user_message("AWS_CREDENTIALS_ERROR"),
                category=ErrorCategory.AWS_SERVICE,
                severity=ErrorSeverity.CRITICAL,
                context=context,
                original_exception=error
            )
        
        elif isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
            
            # 특정 AWS 에러 코드별 처리
            if error_code in ['Throttling', 'ThrottlingException', 'TooManyRequestsException']:
                return StandardError(
                    error_code="AWS_THROTTLING_ERROR",
                    message=f"AWS throttling error: {str(error)}",
                    user_message=self._get_user_message("AWS_THROTTLING_ERROR"),
                    category=ErrorCategory.AWS_SERVICE,
                    severity=ErrorSeverity.WARNING,
                    context={**context, "aws_error_code": error_code},
                    original_exception=error
                )
            
            elif error_code in ['AccessDenied', 'UnauthorizedOperation', 'Forbidden']:
                return StandardError(
                    error_code="AWS_PERMISSION_ERROR",
                    message=f"AWS permission error: {str(error)}",
                    user_message=self._get_user_message("AWS_PERMISSION_ERROR"),
                    category=ErrorCategory.AWS_SERVICE,
                    severity=ErrorSeverity.ERROR,
                    context={**context, "aws_error_code": error_code},
                    original_exception=error
                )
            
            else:
                return StandardError(
                    error_code="AWS_CONNECTION_ERROR",
                    message=f"AWS service error: {str(error)}",
                    user_message=self._get_user_message("AWS_CONNECTION_ERROR"),
                    category=ErrorCategory.AWS_SERVICE,
                    severity=ErrorSeverity.ERROR,
                    context={**context, "aws_error_code": error_code},
                    original_exception=error
                )
        
        elif isinstance(error, BotoCoreError):
            return StandardError(
                error_code="AWS_CONNECTION_ERROR",
                message=f"AWS connection error: {str(error)}",
                user_message=self._get_user_message("AWS_CONNECTION_ERROR"),
                category=ErrorCategory.AWS_SERVICE,
                severity=ErrorSeverity.ERROR,
                context=context,
                original_exception=error
            )
        
        else:
            return self.handle_generic_error(error, context)
    
    def handle_model_error(self, error: Exception, context: Dict[str, Any] = None) -> StandardError:
        """
        AI 모델 관련 에러 처리
        
        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        context = context or {}
        
        # 타임아웃 에러 처리
        if "timeout" in str(error).lower() or "timed out" in str(error).lower():
            return StandardError(
                error_code="MODEL_TIMEOUT_ERROR",
                message=f"Model inference timeout: {str(error)}",
                user_message=self._get_user_message("MODEL_TIMEOUT_ERROR"),
                category=ErrorCategory.MODEL_INFERENCE,
                severity=ErrorSeverity.WARNING,
                context=context,
                original_exception=error
            )
        
        # 모델 추론 에러
        elif isinstance(error, ClientError):
            # AWS Bedrock 모델 에러는 AWS 에러로 처리
            return self.handle_aws_error(error, context)
        
        else:
            return StandardError(
                error_code="MODEL_INFERENCE_ERROR",
                message=f"Model inference error: {str(error)}",
                user_message=self._get_user_message("MODEL_INFERENCE_ERROR"),
                category=ErrorCategory.MODEL_INFERENCE,
                severity=ErrorSeverity.ERROR,
                context=context,
                original_exception=error
            )
    
    def handle_config_error(self, error: Exception, context: Dict[str, Any] = None) -> StandardError:
        """
        설정 관련 에러 처리
        
        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        context = context or {}
        
        if isinstance(error, ValueError):
            return StandardError(
                error_code="CONFIG_INVALID_ERROR",
                message=f"Configuration validation error: {str(error)}",
                user_message=self._get_user_message("CONFIG_INVALID_ERROR"),
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.ERROR,
                context=context,
                original_exception=error
            )
        
        elif isinstance(error, KeyError):
            return StandardError(
                error_code="CONFIG_MISSING_ERROR",
                message=f"Missing configuration: {str(error)}",
                user_message=self._get_user_message("CONFIG_MISSING_ERROR"),
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.ERROR,
                context=context,
                original_exception=error
            )
        
        else:
            return StandardError(
                error_code="CONFIG_INVALID_ERROR",
                message=f"Configuration error: {str(error)}",
                user_message=self._get_user_message("CONFIG_INVALID_ERROR"),
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.ERROR,
                context=context,
                original_exception=error
            )
    
    def handle_network_error(self, error: Exception, context: Dict[str, Any] = None) -> StandardError:
        """
        네트워크 관련 에러 처리
        
        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        context = context or {}
        
        return StandardError(
            error_code="NETWORK_ERROR",
            message=f"Network error: {str(error)}",
            user_message=self._get_user_message("NETWORK_ERROR"),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.WARNING,
            context=context,
            original_exception=error
        )
    
    def handle_validation_error(self, error: Exception, context: Dict[str, Any] = None) -> StandardError:
        """
        입력 검증 에러 처리
        
        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        context = context or {}
        
        return StandardError(
            error_code="VALIDATION_ERROR",
            message=f"Validation error: {str(error)}",
            user_message=self._get_user_message("VALIDATION_ERROR"),
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            context=context,
            original_exception=error
        )
    
    def handle_generic_error(self, error: Exception, context: Dict[str, Any] = None) -> StandardError:
        """
        일반적인 에러 처리
        
        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        context = context or {}
        
        return StandardError(
            error_code="SYSTEM_ERROR",
            message=f"System error: {str(error)}",
            user_message=self._get_user_message("SYSTEM_ERROR"),
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            context=context,
            original_exception=error
        )
    
    def log_error(self, error: StandardError) -> None:
        """
        에러 로깅
        
        Args:
            error: 로깅할 표준화된 에러
        """
        log_message = (
            f"[{error.category.value}] {error.error_code}: {error.message}"
        )
        
        # 컨텍스트 정보 추가
        if error.context:
            context_str = ", ".join([f"{k}={v}" for k, v in error.context.items()])
            log_message += f" | Context: {context_str}"
        
        # 심각도에 따른 로깅 레벨 결정
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # 스택 트레이스가 있는 경우 디버그 레벨로 로깅
        if error.stack_trace and error.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"Stack trace for {error.error_code}:\n{error.stack_trace}")
    
    def get_user_message(self, error_code: str, lang: str = "ko") -> str:
        """
        사용자 친화적 에러 메시지 반환
        
        Args:
            error_code: 에러 코드
            lang: 언어 코드 ("ko" 또는 "en")
            
        Returns:
            str: 사용자 친화적 메시지
        """
        return self._get_user_message(error_code, lang)
    
    def _get_user_message(self, error_code: str, lang: str = "ko") -> str:
        """
        내부용 사용자 메시지 조회
        
        Args:
            error_code: 에러 코드
            lang: 언어 코드
            
        Returns:
            str: 사용자 친화적 메시지
        """
        messages = self._user_messages.get(lang, self._user_messages["ko"])
        return messages.get(error_code, messages["UNKNOWN_ERROR"])
    
    def create_error_from_exception(self, exception: Exception, 
                                  context: Dict[str, Any] = None) -> StandardError:
        """
        예외로부터 적절한 StandardError 생성
        
        Args:
            exception: 발생한 예외
            context: 추가 컨텍스트 정보
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        # AWS 관련 에러
        if isinstance(exception, (ClientError, NoCredentialsError, BotoCoreError)):
            return self.handle_aws_error(exception, context)
        
        # 설정 관련 에러
        elif isinstance(exception, (ValueError, KeyError)) and context and context.get("category") == "config":
            return self.handle_config_error(exception, context)
        
        # 네트워크 관련 에러
        elif "connection" in str(exception).lower() or "network" in str(exception).lower():
            return self.handle_network_error(exception, context)
        
        # 모델 관련 에러 (컨텍스트로 판단)
        elif context and context.get("category") == "model":
            return self.handle_model_error(exception, context)
        
        # 검증 관련 에러
        elif isinstance(exception, ValueError):
            return self.handle_validation_error(exception, context)
        
        # 기타 에러
        else:
            return self.handle_generic_error(exception, context)


# 전역 에러 핸들러 인스턴스
_global_error_handler = None


def get_error_handler(logger: Optional[logging.Logger] = None) -> ErrorHandler:
    """
    전역 에러 핸들러 인스턴스 반환 (싱글톤 패턴)
    
    Args:
        logger: 로깅에 사용할 로거 인스턴스
        
    Returns:
        ErrorHandler: 에러 핸들러 인스턴스
    """
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(logger)
    
    return _global_error_handler