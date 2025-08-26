"""
설정 데이터 모델 정의

이 모듈은 애플리케이션의 설정 구조를 정의하는 데이터클래스들을 포함합니다.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import os


@dataclass
class AWSConfig:
    """AWS 관련 설정 데이터 모델"""
    region: str = "us-east-1"
    bedrock_models: Dict[str, str] = field(default_factory=lambda: {
        "nova_micro": "us.amazon.nova-micro-v1:0",
        "nova_pro": "us.amazon.nova-pro-v1:0"
    })
    knowledge_base_id: str = "SJJP9YYPHX"
    s3_bucket: str = ""
    
    def validate(self) -> List[str]:
        """AWS 설정 검증"""
        errors = []
        
        if not self.region:
            errors.append("AWS region이 설정되지 않았습니다.")
        
        if not self.knowledge_base_id:
            errors.append("Knowledge Base ID가 설정되지 않았습니다.")
            
        if not self.bedrock_models:
            errors.append("Bedrock 모델 설정이 없습니다.")
        
        return errors


@dataclass
class UIConfig:
    """UI 관련 설정 데이터 모델"""
    page_title: str = "글로벌 CS 챗봇 🌍"
    page_icon: str = "🌍"
    layout: str = "wide"
    theme: Dict[str, Any] = field(default_factory=lambda: {
        "primaryColor": "#667eea",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f0f2f6"
    })
    
    def validate(self) -> List[str]:
        """UI 설정 검증"""
        errors = []
        
        if not self.page_title:
            errors.append("페이지 제목이 설정되지 않았습니다.")
            
        if self.layout not in ["wide", "centered"]:
            errors.append("레이아웃은 'wide' 또는 'centered'여야 합니다.")
        
        return errors


@dataclass
class LoggingConfig:
    """로깅 관련 설정 데이터 모델"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    def validate(self) -> List[str]:
        """로깅 설정 검증"""
        errors = []
        
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level not in valid_levels:
            errors.append(f"로깅 레벨은 {valid_levels} 중 하나여야 합니다.")
        
        if self.max_file_size <= 0:
            errors.append("최대 파일 크기는 0보다 커야 합니다.")
            
        if self.backup_count < 0:
            errors.append("백업 파일 개수는 0 이상이어야 합니다.")
        
        return errors


@dataclass
class CacheConfig:
    """캐시 관련 설정 데이터 모델"""
    enabled: bool = True
    ttl_seconds: int = 3600  # 1시간
    max_size: int = 1000
    
    def validate(self) -> List[str]:
        """캐시 설정 검증"""
        errors = []
        
        if self.ttl_seconds <= 0:
            errors.append("캐시 TTL은 0보다 커야 합니다.")
            
        if self.max_size <= 0:
            errors.append("캐시 최대 크기는 0보다 커야 합니다.")
        
        return errors


@dataclass
class AppConfig:
    """전체 애플리케이션 설정 데이터 모델"""
    aws: AWSConfig = field(default_factory=AWSConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    environment: str = "development"
    debug: bool = False
    
    def validate(self) -> List[str]:
        """전체 설정 검증"""
        errors = []
        
        # 각 하위 설정 검증
        errors.extend(self.aws.validate())
        errors.extend(self.ui.validate())
        errors.extend(self.logging.validate())
        errors.extend(self.cache.validate())
        
        # 환경 설정 검증
        valid_environments = ["development", "staging", "production", "test"]
        if self.environment not in valid_environments:
            errors.append(f"환경은 {valid_environments} 중 하나여야 합니다.")
        
        return errors
    
    def get_required_env_vars(self) -> List[str]:
        """필수 환경 변수 목록 반환"""
        required_vars = []
        
        # AWS 관련 필수 환경 변수
        if not self.aws.region:
            required_vars.append("AWS_DEFAULT_REGION")
            
        if not self.aws.knowledge_base_id:
            required_vars.append("KNOWLEDGE_BASE_ID")
        
        return required_vars