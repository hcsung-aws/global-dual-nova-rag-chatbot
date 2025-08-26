"""
에러 처리 및 로깅 통합 유틸리티

이 모듈은 에러 처리와 로깅을 통합하여 사용하기 쉬운 
데코레이터와 컨텍스트 매니저를 제공합니다.
"""

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, Type, Union

from .error_handler import ErrorHandler, StandardError, get_error_handler
from .logger import StandardLogger, get_logger


def handle_errors(
    error_handler: Optional[ErrorHandler] = None,
    logger: Optional[StandardLogger] = None,
    category: Optional[str] = None,
    reraise: bool = True,
    return_on_error: Any = None
):
    """
    에러 처리 데코레이터
    
    Args:
        error_handler: 사용할 에러 핸들러 (None이면 전역 인스턴스 사용)
        logger: 사용할 로거 (None이면 전역 인스턴스 사용)
        category: 에러 카테고리 ("aws", "model", "config" 등)
        reraise: 에러를 다시 발생시킬지 여부
        return_on_error: 에러 발생 시 반환할 값
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _error_handler = error_handler or get_error_handler()
            _logger = logger or get_logger()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 컨텍스트 정보 생성
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
                
                if category:
                    context["category"] = category
                
                # 적절한 에러 처리기 선택
                if category == "aws":
                    standard_error = _error_handler.handle_aws_error(e, context)
                elif category == "model":
                    standard_error = _error_handler.handle_model_error(e, context)
                elif category == "config":
                    standard_error = _error_handler.handle_config_error(e, context)
                elif category == "network":
                    standard_error = _error_handler.handle_network_error(e, context)
                elif category == "validation":
                    standard_error = _error_handler.handle_validation_error(e, context)
                else:
                    standard_error = _error_handler.create_error_from_exception(e, context)
                
                # 에러 로깅
                _logger.log_error(standard_error)
                
                if reraise:
                    raise
                else:
                    return return_on_error
        
        return wrapper
    return decorator


def log_performance(
    logger: Optional[StandardLogger] = None,
    operation_name: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False
):
    """
    성능 로깅 데코레이터
    
    Args:
        logger: 사용할 로거 (None이면 전역 인스턴스 사용)
        operation_name: 작업 이름 (None이면 함수명 사용)
        log_args: 함수 인자를 로깅할지 여부
        log_result: 함수 결과를 로깅할지 여부
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger()
            _operation_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # 컨텍스트 정보 준비
            context = {
                "function": func.__name__,
                "module": func.__module__
            }
            
            if log_args:
                context["args_count"] = len(args)
                context["kwargs_keys"] = list(kwargs.keys())
            
            start_time = time.time()
            success = True
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                
                if log_result and result is not None:
                    context["result_type"] = type(result).__name__
                    if hasattr(result, '__len__'):
                        try:
                            context["result_length"] = len(result)
                        except:
                            pass
                
                _logger.log_performance(_operation_name, duration, success, **context)
        
        return wrapper
    return decorator


@contextmanager
def error_context(
    category: str,
    operation: str,
    error_handler: Optional[ErrorHandler] = None,
    logger: Optional[StandardLogger] = None,
    **context_kwargs
):
    """
    에러 처리 컨텍스트 매니저
    
    Args:
        category: 에러 카테고리
        operation: 작업 이름
        error_handler: 사용할 에러 핸들러
        logger: 사용할 로거
        **context_kwargs: 추가 컨텍스트 정보
    """
    _error_handler = error_handler or get_error_handler()
    _logger = logger or get_logger()
    
    context = {
        "operation": operation,
        "category": category,
        **context_kwargs
    }
    
    try:
        yield
    except Exception as e:
        # 카테고리별 에러 처리
        if category == "aws":
            standard_error = _error_handler.handle_aws_error(e, context)
        elif category == "model":
            standard_error = _error_handler.handle_model_error(e, context)
        elif category == "config":
            standard_error = _error_handler.handle_config_error(e, context)
        elif category == "network":
            standard_error = _error_handler.handle_network_error(e, context)
        elif category == "validation":
            standard_error = _error_handler.handle_validation_error(e, context)
        else:
            standard_error = _error_handler.handle_generic_error(e, context)
        
        # 에러 로깅
        _logger.log_error(standard_error)
        
        # 원본 예외 다시 발생
        raise


@contextmanager
def performance_context(
    operation: str,
    logger: Optional[StandardLogger] = None,
    **context_kwargs
):
    """
    성능 측정 컨텍스트 매니저
    
    Args:
        operation: 작업 이름
        logger: 사용할 로거
        **context_kwargs: 추가 컨텍스트 정보
    """
    _logger = logger or get_logger()
    
    with _logger.performance_timer(operation, **context_kwargs):
        yield


def log_aws_api_call(
    service: str,
    operation: str,
    logger: Optional[StandardLogger] = None
):
    """
    AWS API 호출 로깅 데코레이터
    
    Args:
        service: AWS 서비스 이름
        operation: API 작업 이름
        logger: 사용할 로거
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger()
            
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                _logger.log_api_call(service, operation, success)
        
        return wrapper
    return decorator


def log_model_usage(
    model_id: str,
    logger: Optional[StandardLogger] = None
):
    """
    모델 사용량 로깅 데코레이터
    
    Args:
        model_id: 모델 ID
        logger: 사용할 로거
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger()
            
            result = func(*args, **kwargs)
            
            # 결과에서 토큰 사용량 정보 추출
            if isinstance(result, dict) and 'usage' in result:
                usage = result['usage']
                tokens = {}
                
                # 일반적인 토큰 사용량 필드들
                if 'inputTokens' in usage:
                    tokens['input'] = usage['inputTokens']
                if 'outputTokens' in usage:
                    tokens['output'] = usage['outputTokens']
                if 'totalTokens' in usage:
                    tokens['total'] = usage['totalTokens']
                if 'cacheReadInputTokenCount' in usage:
                    tokens['cache_read'] = usage['cacheReadInputTokenCount']
                if 'cacheWriteInputTokenCount' in usage:
                    tokens['cache_write'] = usage['cacheWriteInputTokenCount']
                
                if tokens:
                    _logger.log_model_usage(model_id, tokens)
            
            return result
        
        return wrapper
    return decorator


class ErrorLoggingMixin:
    """
    에러 처리 및 로깅 기능을 제공하는 믹스인 클래스
    
    이 클래스를 상속받으면 표준화된 에러 처리와 로깅 기능을 사용할 수 있습니다.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._error_handler = get_error_handler()
        self._logger = get_logger()
    
    def handle_error(self, error: Exception, category: str = None, context: Dict[str, Any] = None) -> StandardError:
        """
        에러 처리
        
        Args:
            error: 발생한 예외
            category: 에러 카테고리
            context: 추가 컨텍스트 정보
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        context = context or {}
        context["class"] = self.__class__.__name__
        
        if category == "aws":
            standard_error = self._error_handler.handle_aws_error(error, context)
        elif category == "model":
            standard_error = self._error_handler.handle_model_error(error, context)
        elif category == "config":
            standard_error = self._error_handler.handle_config_error(error, context)
        else:
            standard_error = self._error_handler.create_error_from_exception(error, context)
        
        self._logger.log_error(standard_error)
        return standard_error
    
    def log_info(self, message: str, **kwargs):
        """정보 로깅"""
        kwargs["class"] = self.__class__.__name__
        self._logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """경고 로깅"""
        kwargs["class"] = self.__class__.__name__
        self._logger.warning(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """에러 로깅"""
        kwargs["class"] = self.__class__.__name__
        self._logger.error(message, **kwargs)
    
    def log_performance(self, operation: str, duration: float, success: bool = True, **kwargs):
        """성능 로깅"""
        kwargs["class"] = self.__class__.__name__
        self._logger.log_performance(operation, duration, success, **kwargs)


# 편의 함수들
def safe_execute(func: Callable, *args, default=None, category: str = None, **kwargs):
    """
    안전한 함수 실행 (에러 발생 시 기본값 반환)
    
    Args:
        func: 실행할 함수
        *args: 함수 인자
        default: 에러 발생 시 반환할 기본값
        category: 에러 카테고리
        **kwargs: 함수 키워드 인자
        
    Returns:
        함수 실행 결과 또는 기본값
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler = get_error_handler()
        logger = get_logger()
        
        context = {
            "function": func.__name__ if hasattr(func, '__name__') else str(func),
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys())
        }
        
        if category:
            context["category"] = category
        
        standard_error = error_handler.create_error_from_exception(e, context)
        logger.log_error(standard_error)
        
        return default


def get_user_friendly_error(error: Exception, lang: str = "ko") -> str:
    """
    사용자 친화적 에러 메시지 반환
    
    Args:
        error: 발생한 예외
        lang: 언어 코드
        
    Returns:
        str: 사용자 친화적 메시지
    """
    error_handler = get_error_handler()
    standard_error = error_handler.create_error_from_exception(error)
    return error_handler.get_user_message(standard_error.error_code, lang)