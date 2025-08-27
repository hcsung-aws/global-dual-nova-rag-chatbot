"""
AWS 클라이언트 관리 시스템

이 모듈은 AWS 클라이언트의 초기화, 재사용, 헬스체크를 담당하는 싱글톤 패턴의 관리자를 제공합니다.
기존의 @st.cache_resource 방식을 대체하여 더 명시적이고 테스트 가능한 클라이언트 관리를 구현합니다.
"""

import boto3
import logging
import time
from typing import Dict, Optional, Any, List
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from threading import Lock


class AWSClientManager:
    """
    AWS 클라이언트 싱글톤 관리자
    
    이 클래스는 싱글톤 패턴을 사용하여 AWS 클라이언트를 한 번만 초기화하고 재사용합니다.
    클라이언트 초기화, 헬스체크, 에러 처리 및 재시도 로직을 제공합니다.
    
    요구사항:
    - 3.1: AWS 클라이언트 재사용을 통한 성능 최적화
    - 3.2: 필요한 클라이언트만 초기화
    - 3.3: 적절한 에러 처리와 재시도 로직
    """
    
    _instance: Optional['AWSClientManager'] = None
    _lock = Lock()
    
    def __new__(cls) -> 'AWSClientManager':
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """초기화 (싱글톤이므로 한 번만 실행됨)"""
        if not getattr(self, '_initialized', False):
            self._clients: Dict[str, Any] = {}
            self._config = self._create_default_config()
            self._logger = self._setup_logger()
            self._initialized = True
            self._logger.info("AWSClientManager 초기화 완료")
    
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('AWSClientManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _create_default_config(self) -> Config:
        """기본 AWS 설정 생성"""
        return Config(
            read_timeout=60,
            connect_timeout=10,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=50
        )
    
    def get_client(self, service_name: str, region_name: str = 'us-east-1', 
                   config: Optional[Config] = None) -> Any:
        """
        AWS 클라이언트 반환 (없으면 생성)
        
        Args:
            service_name: AWS 서비스 이름 (예: 's3', 'bedrock-runtime')
            region_name: AWS 리전 (기본값: us-east-1)
            config: 사용자 정의 Config (기본값: None)
            
        Returns:
            boto3 클라이언트 인스턴스
            
        Raises:
            NoCredentialsError: AWS 자격 증명이 없는 경우
            ClientError: AWS 클라이언트 생성 실패
        """
        client_key = f"{service_name}_{region_name}"
        
        if client_key not in self._clients:
            try:
                self._logger.info(f"새로운 AWS 클라이언트 생성: {service_name} (리전: {region_name})")
                
                # 사용자 정의 config가 없으면 기본 config 사용
                client_config = config or self._config
                
                client = boto3.client(
                    service_name,
                    region_name=region_name,
                    config=client_config
                )
                
                # 클라이언트 생성 후 간단한 헬스체크
                self._validate_client(client, service_name)
                
                self._clients[client_key] = client
                self._logger.info(f"AWS 클라이언트 생성 완료: {service_name}")
                
            except NoCredentialsError as e:
                self._logger.error(f"AWS 자격 증명 오류: {e}")
                raise
            except ClientError as e:
                self._logger.error(f"AWS 클라이언트 생성 오류 ({service_name}): {e}")
                raise
            except Exception as e:
                self._logger.error(f"예상치 못한 오류 ({service_name}): {e}")
                raise
        
        return self._clients[client_key]
    
    def _validate_client(self, client: Any, service_name: str) -> None:
        """
        클라이언트 유효성 검사
        
        Args:
            client: 검증할 boto3 클라이언트
            service_name: 서비스 이름
            
        Raises:
            ClientError: 클라이언트 검증 실패
        """
        try:
            # 서비스별 간단한 헬스체크
            if service_name == 's3':
                client.list_buckets()
            elif service_name == 'bedrock-runtime':
                # Bedrock Runtime은 invoke_model 메서드 존재 여부만 확인
                if not hasattr(client, 'invoke_model'):
                    raise AttributeError("bedrock-runtime 클라이언트에 invoke_model 메서드가 없습니다")
                self._logger.info(f"✅ Bedrock Runtime 헬스체크 성공 - invoke_model 메서드 확인됨")
            elif service_name == 'bedrock':
                # Bedrock은 list_foundation_models로 헬스체크
                try:
                    client.list_foundation_models()
                    self._logger.info(f"✅ Bedrock 헬스체크 성공")
                except Exception as bedrock_error:
                    self._logger.warning(f"⚠️ Bedrock 헬스체크 실패: {bedrock_error}")
                    raise
            elif service_name == 'secretsmanager':
                # Secrets Manager는 list_secrets로 헬스체크 (빈 결과도 OK)
                client.list_secrets(MaxResults=1)
            elif service_name == 'bedrock-agent-runtime':
                # Bedrock Agent Runtime은 특별한 헬스체크 없이 통과
                pass
            elif service_name == 'cloudwatch':
                # CloudWatch는 list_metrics로 헬스체크 (MaxRecords 파라미터 제거)
                client.list_metrics()
            else:
                # 기타 서비스는 기본적인 메타데이터 확인
                client.meta.region_name
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                # 권한 부족은 경고로만 처리 (클라이언트 자체는 유효)
                self._logger.warning(f"권한 부족하지만 클라이언트는 유효함: {service_name}")
            else:
                self._logger.error(f"클라이언트 검증 실패: {service_name} - {error_code}: {e}")
                raise
    
    def initialize_clients(self, services: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        여러 AWS 클라이언트를 한 번에 초기화
        
        Args:
            services: 초기화할 서비스 목록 (기본값: 기본 서비스들)
            
        Returns:
            초기화된 클라이언트들의 딕셔너리
        """
        if services is None:
            # 기본 서비스 목록 (기존 get_aws_clients()와 동일)
            services = ['s3', 'bedrock-runtime', 'secretsmanager']
        
        clients = {}
        failed_services = []
        
        for service in services:
            try:
                client = self.get_client(service)
                clients[service] = client
                self._logger.info(f"✅ 클라이언트 초기화 성공: {service}")
            except Exception as e:
                self._logger.error(f"❌ 클라이언트 초기화 실패: {service} - {e}")
                failed_services.append(service)
                # 실패한 클라이언트는 None으로 설정하지 않고 제외
        
        # 중요한 서비스가 실패한 경우 경고
        critical_services = ['bedrock-runtime']
        failed_critical = [s for s in failed_services if s in critical_services]
        
        if failed_critical:
            self._logger.warning(f"⚠️ 중요한 서비스 초기화 실패: {failed_critical}")
            # 재시도 로직
            for service in failed_critical:
                try:
                    self._logger.info(f"🔄 {service} 재시도 중...")
                    client = self.get_client_with_retry(service, max_retries=2)
                    clients[service] = client
                    self._logger.info(f"✅ {service} 재시도 성공")
                except Exception as e:
                    self._logger.error(f"❌ {service} 재시도 실패: {e}")
        
        return clients
    
    def health_check(self) -> Dict[str, bool]:
        """
        모든 초기화된 클라이언트의 헬스체크 수행
        
        Returns:
            각 클라이언트의 헬스체크 결과
        """
        health_status = {}
        
        for client_key, client in self._clients.items():
            service_name = client_key.split('_')[0]  # service_name_region에서 service_name 추출
            
            try:
                self._validate_client(client, service_name)
                health_status[client_key] = True
                self._logger.info(f"헬스체크 성공: {client_key}")
            except Exception as e:
                health_status[client_key] = False
                self._logger.error(f"헬스체크 실패: {client_key} - {e}")
        
        return health_status
    
    def get_client_with_retry(self, service_name: str, max_retries: int = 3, 
                             retry_delay: float = 1.0) -> Any:
        """
        재시도 로직이 포함된 클라이언트 반환
        
        Args:
            service_name: AWS 서비스 이름
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간격 (초)
            
        Returns:
            boto3 클라이언트 인스턴스
            
        Raises:
            Exception: 모든 재시도 실패 시
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.get_client(service_name)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    self._logger.warning(
                        f"클라이언트 생성 실패 (시도 {attempt + 1}/{max_retries + 1}): {service_name} - {e}"
                    )
                    time.sleep(retry_delay * (2 ** attempt))  # 지수 백오프
                else:
                    self._logger.error(f"모든 재시도 실패: {service_name} - {e}")
        
        raise last_exception
    
    def clear_clients(self) -> None:
        """모든 클라이언트 캐시 초기화"""
        self._clients.clear()
        self._logger.info("모든 AWS 클라이언트 캐시 초기화 완료")
    
    def get_client_info(self) -> Dict[str, Dict[str, Any]]:
        """
        현재 초기화된 클라이언트들의 정보 반환
        
        Returns:
            클라이언트 정보 딕셔너리
        """
        info = {}
        for client_key, client in self._clients.items():
            try:
                info[client_key] = {
                    'service_name': client.meta.service_model.service_name,
                    'region_name': client.meta.region_name,
                    'endpoint_url': client.meta.endpoint_url,
                    'api_version': client.meta.service_model.api_version
                }
            except Exception as e:
                info[client_key] = {'error': str(e)}
        
        return info


# 전역 인스턴스 생성 함수
def get_aws_client_manager() -> AWSClientManager:
    """
    AWSClientManager 싱글톤 인스턴스 반환
    
    Returns:
        AWSClientManager 인스턴스
    """
    return AWSClientManager()


# 기존 get_aws_clients() 함수와 호환성을 위한 래퍼 함수
def get_aws_clients() -> Dict[str, Any]:
    """
    기존 get_aws_clients() 함수와의 호환성을 위한 래퍼
    
    Returns:
        AWS 클라이언트 딕셔너리 (기존 형식과 동일)
    """
    manager = get_aws_client_manager()
    return manager.initialize_clients()