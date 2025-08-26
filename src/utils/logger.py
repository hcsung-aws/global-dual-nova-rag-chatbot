"""
표준화된 로깅 시스템

이 모듈은 애플리케이션 전반에 걸쳐 일관된 로그 형식과 
성능 및 사용량 로깅 기능을 제공합니다.
"""

import logging
import logging.handlers
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import threading
from contextlib import contextmanager

from .error_handler import StandardError


@dataclass
class LogEntry:
    """표준화된 로그 엔트리 구조"""
    timestamp: datetime
    level: str
    message: str
    category: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "category": self.category,
            "context": self.context,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id
        }


@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터 구조"""
    operation: str
    duration: float
    timestamp: datetime
    success: bool
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "operation": self.operation,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "context": self.context
        }


@dataclass
class UsageMetric:
    """사용량 메트릭 데이터 구조"""
    metric_type: str  # "token_usage", "api_call", "user_query" 등
    value: Union[int, float]
    unit: str  # "tokens", "calls", "queries" 등
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "metric_type": self.metric_type,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }


class StandardLogger:
    """표준화된 로깅 시스템"""
    
    def __init__(self, 
                 name: str = "chatbot_app",
                 level: str = "INFO",
                 log_dir: str = "logs",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = True):
        """
        표준화된 로거 초기화
        
        Args:
            name: 로거 이름
            level: 로깅 레벨
            log_dir: 로그 파일 디렉토리
            max_file_size: 최대 파일 크기 (바이트)
            backup_count: 백업 파일 개수
            enable_console: 콘솔 출력 활성화
            enable_file: 파일 출력 활성화
            enable_json: JSON 형식 로깅 활성화
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.enable_json = enable_json
        
        # 로그 디렉토리 생성
        self.log_dir.mkdir(exist_ok=True)
        
        # 메인 로거 설정
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 기존 핸들러 제거 (중복 방지)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 포매터 설정
        self._setup_formatters()
        
        # 핸들러 설정
        if enable_console:
            self._setup_console_handler()
        
        if enable_file:
            self._setup_file_handlers(max_file_size, backup_count)
        
        # 성능 및 사용량 로거 설정
        self._setup_metric_loggers(max_file_size, backup_count)
        
        # 스레드 로컬 컨텍스트
        self._local = threading.local()
        
        self.logger.info(f"StandardLogger 초기화 완료: {name}")
    
    def _setup_formatters(self):
        """포매터 설정"""
        # 일반 로그 포매터
        self.formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # JSON 포매터 (구조화된 로깅용)
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # 추가 컨텍스트 정보가 있으면 포함
                if hasattr(record, 'context'):
                    log_data["context"] = record.context
                
                if hasattr(record, 'user_id'):
                    log_data["user_id"] = record.user_id
                
                if hasattr(record, 'session_id'):
                    log_data["session_id"] = record.session_id
                
                return json.dumps(log_data, ensure_ascii=False)
        
        self.json_formatter = JsonFormatter()
    
    def _setup_console_handler(self):
        """콘솔 핸들러 설정"""
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handlers(self, max_file_size: int, backup_count: int):
        """파일 핸들러 설정"""
        # 일반 로그 파일
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
        
        # JSON 로그 파일 (구조화된 로깅)
        if self.enable_json:
            json_log_file = self.log_dir / f"{self.name}_structured.log"
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            json_handler.setFormatter(self.json_formatter)
            self.logger.addHandler(json_handler)
    
    def _setup_metric_loggers(self, max_file_size: int, backup_count: int):
        """메트릭 전용 로거 설정"""
        # 성능 메트릭 로거
        self.performance_logger = logging.getLogger(f"{self.name}.performance")
        self.performance_logger.setLevel(logging.INFO)
        
        perf_file = self.log_dir / f"{self.name}_performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        perf_handler.setFormatter(self.json_formatter)
        self.performance_logger.addHandler(perf_handler)
        
        # 사용량 메트릭 로거
        self.usage_logger = logging.getLogger(f"{self.name}.usage")
        self.usage_logger.setLevel(logging.INFO)
        
        usage_file = self.log_dir / f"{self.name}_usage.log"
        usage_handler = logging.handlers.RotatingFileHandler(
            usage_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        usage_handler.setFormatter(self.json_formatter)
        self.usage_logger.addHandler(usage_handler)
    
    def set_context(self, **kwargs):
        """현재 스레드의 로깅 컨텍스트 설정"""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        self._local.context.update(kwargs)
    
    def clear_context(self):
        """현재 스레드의 로깅 컨텍스트 초기화"""
        if hasattr(self._local, 'context'):
            self._local.context.clear()
    
    def _get_context(self) -> Dict[str, Any]:
        """현재 스레드의 컨텍스트 반환"""
        if hasattr(self._local, 'context'):
            return self._local.context.copy()
        return {}
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """컨텍스트와 함께 로깅"""
        context = self._get_context()
        context.update(kwargs)
        
        # LogRecord에 추가 정보 설정
        extra = {
            'context': context
        }
        
        # 사용자 정보가 컨텍스트에 있으면 추가
        if 'user_id' in context:
            extra['user_id'] = context['user_id']
        
        if 'session_id' in context:
            extra['session_id'] = context['session_id']
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """디버그 로깅"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """정보 로깅"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """경고 로깅"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """에러 로깅"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """치명적 에러 로깅"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def log_error(self, error: StandardError):
        """표준화된 에러 로깅"""
        context = {
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value,
            "context": error.context
        }
        
        if error.original_exception:
            context["exception_type"] = type(error.original_exception).__name__
        
        message = f"[{error.category.value}] {error.error_code}: {error.message}"
        
        # 심각도에 따른 로깅
        if error.severity.value == "CRITICAL":
            self.critical(message, **context)
        elif error.severity.value == "ERROR":
            self.error(message, **context)
        elif error.severity.value == "WARNING":
            self.warning(message, **context)
        else:
            self.info(message, **context)
    
    def log_request(self, user_query: str, response_time: float, **kwargs):
        """사용자 요청 로깅"""
        context = {
            "user_query": user_query,
            "response_time": response_time,
            **kwargs
        }
        
        self.info(f"사용자 요청 처리 완료 (응답시간: {response_time:.2f}초)", **context)
    
    def log_model_usage(self, model_id: str, tokens: Dict[str, int], **kwargs):
        """모델 사용량 로깅"""
        # 사용량 메트릭 생성
        for token_type, count in tokens.items():
            metric = UsageMetric(
                metric_type=f"token_usage_{token_type}",
                value=count,
                unit="tokens",
                timestamp=datetime.now(),
                context={
                    "model_id": model_id,
                    "token_type": token_type,
                    **kwargs
                }
            )
            
            # 사용량 로거에 기록
            self.usage_logger.info(
                f"토큰 사용량: {model_id} - {token_type}: {count}",
                extra={"context": metric.to_dict()}
            )
        
        # 메인 로거에도 요약 정보 기록
        total_tokens = sum(tokens.values())
        self.info(
            f"모델 사용량: {model_id} - 총 {total_tokens:,} 토큰",
            model_id=model_id,
            total_tokens=total_tokens,
            token_breakdown=tokens,
            **kwargs
        )
    
    def log_performance(self, operation: str, duration: float, success: bool = True, **kwargs):
        """성능 메트릭 로깅"""
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            timestamp=datetime.now(),
            success=success,
            context=kwargs
        )
        
        # 성능 로거에 기록
        self.performance_logger.info(
            f"성능 메트릭: {operation} - {duration:.3f}초 ({'성공' if success else '실패'})",
            extra={"context": metric.to_dict()}
        )
        
        # 메인 로거에도 기록 (느린 작업의 경우 경고)
        if duration > 5.0:  # 5초 이상
            self.warning(
                f"느린 작업 감지: {operation} - {duration:.3f}초",
                operation=operation,
                duration=duration,
                success=success,
                **kwargs
            )
        else:
            self.debug(
                f"작업 완료: {operation} - {duration:.3f}초",
                operation=operation,
                duration=duration,
                success=success,
                **kwargs
            )
    
    def log_api_call(self, service: str, operation: str, success: bool = True, **kwargs):
        """API 호출 로깅"""
        metric = UsageMetric(
            metric_type="api_call",
            value=1,
            unit="calls",
            timestamp=datetime.now(),
            context={
                "service": service,
                "operation": operation,
                "success": success,
                **kwargs
            }
        )
        
        # 사용량 로거에 기록
        self.usage_logger.info(
            f"API 호출: {service}.{operation} ({'성공' if success else '실패'})",
            extra={"context": metric.to_dict()}
        )
        
        # 메인 로거에도 기록
        level = self.info if success else self.error
        level(
            f"API 호출: {service}.{operation}",
            service=service,
            operation=operation,
            success=success,
            **kwargs
        )
    
    @contextmanager
    def performance_timer(self, operation: str, **kwargs):
        """성능 측정 컨텍스트 매니저"""
        start_time = time.time()
        success = True
        
        try:
            yield
        except Exception as e:
            success = False
            self.error(f"작업 실패: {operation} - {str(e)}", operation=operation, **kwargs)
            raise
        finally:
            duration = time.time() - start_time
            self.log_performance(operation, duration, success, **kwargs)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """로그 통계 정보 반환"""
        stats = {
            "log_directory": str(self.log_dir),
            "logger_name": self.name,
            "log_level": self.logger.level,
            "handlers": len(self.logger.handlers),
            "log_files": []
        }
        
        # 로그 파일 정보 수집
        for log_file in self.log_dir.glob(f"{self.name}*.log"):
            if log_file.exists():
                stats["log_files"].append({
                    "name": log_file.name,
                    "size": log_file.stat().st_size,
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
        
        return stats


# 전역 로거 인스턴스
_global_logger = None


def get_logger(name: str = "chatbot_app", **kwargs) -> StandardLogger:
    """
    전역 로거 인스턴스 반환 (싱글톤 패턴)
    
    Args:
        name: 로거 이름
        **kwargs: StandardLogger 초기화 인자
        
    Returns:
        StandardLogger: 로거 인스턴스
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = StandardLogger(name, **kwargs)
    
    return _global_logger


def setup_logging_from_config(config: Dict[str, Any]) -> StandardLogger:
    """
    설정으로부터 로깅 시스템 초기화
    
    Args:
        config: 로깅 설정 딕셔너리
        
    Returns:
        StandardLogger: 설정된 로거 인스턴스
    """
    logging_config = config.get("logging", {})
    
    return StandardLogger(
        name=logging_config.get("name", "chatbot_app"),
        level=logging_config.get("level", "INFO"),
        log_dir=logging_config.get("log_dir", "logs"),
        max_file_size=logging_config.get("max_file_size", 10 * 1024 * 1024),
        backup_count=logging_config.get("backup_count", 5),
        enable_console=logging_config.get("enable_console", True),
        enable_file=logging_config.get("enable_file", True),
        enable_json=logging_config.get("enable_json", True)
    )