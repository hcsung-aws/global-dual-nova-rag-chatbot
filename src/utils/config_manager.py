"""
중앙화된 설정 관리 시스템

이 모듈은 애플리케이션의 모든 설정을 중앙에서 관리하는 ConfigManager 클래스를 제공합니다.
환경별 설정 오버라이드, 필수 설정 검증, 에러 처리 기능을 포함합니다.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from src.config.models import AppConfig, AWSConfig, UIConfig, LoggingConfig, CacheConfig


class ConfigManager:
    """중앙화된 설정 관리자"""
    
    _instance = None
    _config: Optional[AppConfig] = None
    _config_loaded = False
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """ConfigManager 초기화"""
        if not self._config_loaded:
            self._logger = logging.getLogger(__name__)
            self._config_paths = self._get_config_paths()
            self._load_config()
            self._config_loaded = True
    
    def _get_config_paths(self) -> List[Path]:
        """설정 파일 경로 목록 반환"""
        base_path = Path(__file__).parent.parent.parent  # 프로젝트 루트
        
        paths = [
            base_path / "config" / "default.json",  # 기본 설정
            base_path / "config" / "settings.json",  # 사용자 설정
        ]
        
        # 환경별 설정 파일
        env = os.getenv("ENVIRONMENT", "development")
        env_config_path = base_path / "config" / f"{env}.json"
        if env_config_path.exists():
            paths.append(env_config_path)
        
        # 로컬 설정 파일 (git에 포함되지 않음)
        local_config_path = base_path / "config" / "local.json"
        if local_config_path.exists():
            paths.append(local_config_path)
        
        return paths
    
    def _load_config(self) -> None:
        """설정 파일들을 로드하고 병합"""
        try:
            # 기본 설정으로 시작
            self._config = AppConfig()
            
            # 설정 파일들을 순서대로 로드하여 병합
            for config_path in self._config_paths:
                if config_path.exists():
                    self._merge_config_file(config_path)
                    self._logger.info(f"설정 파일 로드됨: {config_path}")
            
            # 환경 변수로 오버라이드
            self._apply_env_overrides()
            
            # 설정 검증
            validation_errors = self._config.validate()
            if validation_errors:
                error_msg = "설정 검증 실패:\n" + "\n".join(f"- {error}" for error in validation_errors)
                self._logger.error(error_msg)
                raise ValueError(error_msg)
            
            self._logger.info("설정 로드 및 검증 완료")
            
        except Exception as e:
            self._logger.error(f"설정 로드 중 오류 발생: {e}")
            # 기본 설정으로 fallback
            self._config = AppConfig()
            raise
    
    def _merge_config_file(self, config_path: Path) -> None:
        """설정 파일을 현재 설정에 병합"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            self._merge_dict_to_config(file_config)
            
        except json.JSONDecodeError as e:
            self._logger.error(f"설정 파일 JSON 파싱 오류 ({config_path}): {e}")
            raise
        except Exception as e:
            self._logger.error(f"설정 파일 로드 오류 ({config_path}): {e}")
            raise
    
    def _merge_dict_to_config(self, config_dict: Dict[str, Any]) -> None:
        """딕셔너리를 AppConfig 객체에 병합"""
        if "aws" in config_dict:
            aws_config = config_dict["aws"]
            if isinstance(aws_config, dict):
                for key, value in aws_config.items():
                    if hasattr(self._config.aws, key):
                        setattr(self._config.aws, key, value)
        
        if "ui" in config_dict:
            ui_config = config_dict["ui"]
            if isinstance(ui_config, dict):
                for key, value in ui_config.items():
                    if hasattr(self._config.ui, key):
                        setattr(self._config.ui, key, value)
        
        if "logging" in config_dict:
            logging_config = config_dict["logging"]
            if isinstance(logging_config, dict):
                for key, value in logging_config.items():
                    if hasattr(self._config.logging, key):
                        setattr(self._config.logging, key, value)
        
        if "cache" in config_dict:
            cache_config = config_dict["cache"]
            if isinstance(cache_config, dict):
                for key, value in cache_config.items():
                    if hasattr(self._config.cache, key):
                        setattr(self._config.cache, key, value)
        
        # 최상위 설정들
        for key in ["environment", "debug"]:
            if key in config_dict:
                if hasattr(self._config, key):
                    setattr(self._config, key, config_dict[key])
    
    def _apply_env_overrides(self) -> None:
        """환경 변수로 설정 오버라이드"""
        # AWS 설정
        if os.getenv("AWS_DEFAULT_REGION"):
            self._config.aws.region = os.getenv("AWS_DEFAULT_REGION")
        
        if os.getenv("KNOWLEDGE_BASE_ID"):
            self._config.aws.knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")
        
        if os.getenv("S3_BUCKET"):
            self._config.aws.s3_bucket = os.getenv("S3_BUCKET")
        
        # 환경 설정
        if os.getenv("ENVIRONMENT"):
            self._config.environment = os.getenv("ENVIRONMENT")
        
        if os.getenv("DEBUG"):
            self._config.debug = os.getenv("DEBUG").lower() in ["true", "1", "yes"]
        
        # 로깅 설정
        if os.getenv("LOG_LEVEL"):
            self._config.logging.level = os.getenv("LOG_LEVEL")
        
        if os.getenv("LOG_FILE"):
            self._config.logging.file_path = os.getenv("LOG_FILE")
    
    def get_config(self) -> AppConfig:
        """전체 설정 객체 반환"""
        if self._config is None:
            raise RuntimeError("설정이 로드되지 않았습니다.")
        return self._config
    
    def get_aws_config(self) -> AWSConfig:
        """AWS 설정 반환"""
        return self.get_config().aws
    
    def get_ui_config(self) -> UIConfig:
        """UI 설정 반환"""
        return self.get_config().ui
    
    def get_logging_config(self) -> LoggingConfig:
        """로깅 설정 반환"""
        return self.get_config().logging
    
    def get_cache_config(self) -> CacheConfig:
        """캐시 설정 반환"""
        return self.get_config().cache
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """점 표기법으로 설정값 조회 (예: 'aws.region', 'ui.page_title')"""
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def validate_required_settings(self) -> List[str]:
        """필수 설정 검증 및 누락된 설정 목록 반환"""
        missing_settings = []
        
        # AWS 필수 설정 검증
        if not self._config.aws.region:
            missing_settings.append("AWS region (AWS_DEFAULT_REGION 환경변수 또는 aws.region 설정)")
        
        if not self._config.aws.knowledge_base_id:
            missing_settings.append("Knowledge Base ID (KNOWLEDGE_BASE_ID 환경변수 또는 aws.knowledge_base_id 설정)")
        
        # 필수 환경 변수 검증
        required_env_vars = self._config.get_required_env_vars()
        for env_var in required_env_vars:
            if not os.getenv(env_var):
                missing_settings.append(f"환경변수: {env_var}")
        
        return missing_settings
    
    def reload_config(self) -> None:
        """설정 다시 로드"""
        self._config_loaded = False
        self._load_config()
        self._config_loaded = True
        self._logger.info("설정이 다시 로드되었습니다.")
    
    def get_environment(self) -> str:
        """현재 환경 반환"""
        return self._config.environment if self._config else "development"
    
    def is_debug_mode(self) -> bool:
        """디버그 모드 여부 반환"""
        return self._config.debug if self._config else False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """설정 요약 정보 반환 (민감한 정보 제외)"""
        if not self._config:
            return {}
        
        return {
            "environment": self._config.environment,
            "debug": self._config.debug,
            "aws_region": self._config.aws.region,
            "knowledge_base_id": self._config.aws.knowledge_base_id[:8] + "..." if self._config.aws.knowledge_base_id else None,
            "ui_theme": self._config.ui.theme,
            "logging_level": self._config.logging.level,
            "cache_enabled": self._config.cache.enabled
        }


def get_config_manager() -> ConfigManager:
    """ConfigManager 싱글톤 인스턴스 반환"""
    return ConfigManager()


# 편의 함수들
def get_config() -> AppConfig:
    """전체 설정 객체 반환"""
    return get_config_manager().get_config()


def get_aws_config() -> AWSConfig:
    """AWS 설정 반환"""
    return get_config_manager().get_aws_config()


def get_setting(key: str, default: Any = None) -> Any:
    """설정값 조회"""
    return get_config_manager().get_setting(key, default)