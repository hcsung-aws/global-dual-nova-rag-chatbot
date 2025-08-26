"""
AWSClientManager 단위 테스트

이 테스트는 AWSClientManager의 핵심 기능을 검증합니다:
- 싱글톤 패턴 동작
- 클라이언트 초기화 및 재사용
- 에러 처리 및 재시도 로직
- 헬스체크 기능
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import sys
import os

# 테스트를 위한 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.aws_clients import AWSClientManager, get_aws_client_manager, get_aws_clients


class TestAWSClientManager(unittest.TestCase):
    """AWSClientManager 테스트 클래스"""
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        # 싱글톤 인스턴스 초기화
        AWSClientManager._instance = None
        
    def tearDown(self):
        """각 테스트 후에 실행되는 정리"""
        # 싱글톤 인스턴스 초기화
        AWSClientManager._instance = None
    
    def test_singleton_pattern(self):
        """싱글톤 패턴이 올바르게 동작하는지 테스트"""
        manager1 = AWSClientManager()
        manager2 = AWSClientManager()
        
        # 같은 인스턴스여야 함
        self.assertIs(manager1, manager2)
        
        # get_aws_client_manager()로도 같은 인스턴스 반환
        manager3 = get_aws_client_manager()
        self.assertIs(manager1, manager3)
    
    @patch('boto3.client')
    def test_get_client_success(self, mock_boto_client):
        """클라이언트 생성 성공 테스트"""
        # Mock 클라이언트 설정
        mock_client = Mock()
        mock_client.list_buckets.return_value = {'Buckets': []}
        mock_boto_client.return_value = mock_client
        
        manager = AWSClientManager()
        
        # S3 클라이언트 요청
        client = manager.get_client('s3')
        
        # 클라이언트가 반환되어야 함
        self.assertIsNotNone(client)
        self.assertEqual(client, mock_client)
        
        # boto3.client가 올바른 파라미터로 호출되었는지 확인
        mock_boto_client.assert_called_once()
        
        # 같은 클라이언트를 다시 요청하면 캐시된 것을 반환해야 함
        client2 = manager.get_client('s3')
        self.assertIs(client, client2)
        
        # boto3.client는 한 번만 호출되어야 함 (캐싱 확인)
        self.assertEqual(mock_boto_client.call_count, 1)
    
    @patch('boto3.client')
    def test_get_client_different_regions(self, mock_boto_client):
        """다른 리전의 클라이언트 생성 테스트"""
        mock_client_us = Mock()
        mock_client_eu = Mock()
        mock_client_us.list_buckets.return_value = {'Buckets': []}
        mock_client_eu.list_buckets.return_value = {'Buckets': []}
        
        # 리전별로 다른 클라이언트 반환하도록 설정
        def side_effect(*args, **kwargs):
            if kwargs.get('region_name') == 'us-east-1':
                return mock_client_us
            elif kwargs.get('region_name') == 'eu-west-1':
                return mock_client_eu
            return Mock()
        
        mock_boto_client.side_effect = side_effect
        
        manager = AWSClientManager()
        
        # 다른 리전의 클라이언트 요청
        client_us = manager.get_client('s3', region_name='us-east-1')
        client_eu = manager.get_client('s3', region_name='eu-west-1')
        
        # 다른 인스턴스여야 함
        self.assertIsNot(client_us, client_eu)
        self.assertEqual(client_us, mock_client_us)
        self.assertEqual(client_eu, mock_client_eu)
    
    @patch('boto3.client')
    def test_get_client_credentials_error(self, mock_boto_client):
        """자격 증명 오류 테스트"""
        mock_boto_client.side_effect = NoCredentialsError()
        
        manager = AWSClientManager()
        
        # NoCredentialsError가 발생해야 함
        with self.assertRaises(NoCredentialsError):
            manager.get_client('s3')
    
    @patch('boto3.client')
    def test_get_client_with_retry_success(self, mock_boto_client):
        """재시도 로직 성공 테스트"""
        mock_client = Mock()
        mock_client.list_buckets.return_value = {'Buckets': []}
        
        # 첫 번째 호출은 실패, 두 번째 호출은 성공
        mock_boto_client.side_effect = [ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'ListBuckets'), mock_client]
        
        manager = AWSClientManager()
        
        # 재시도로 성공해야 함
        client = manager.get_client_with_retry('s3', max_retries=2, retry_delay=0.1)
        self.assertEqual(client, mock_client)
        
        # 두 번 호출되었는지 확인
        self.assertEqual(mock_boto_client.call_count, 2)
    
    @patch('boto3.client')
    def test_get_client_with_retry_failure(self, mock_boto_client):
        """재시도 로직 실패 테스트"""
        mock_boto_client.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'ListBuckets')
        
        manager = AWSClientManager()
        
        # 모든 재시도 실패 시 예외 발생
        with self.assertRaises(ClientError):
            manager.get_client_with_retry('s3', max_retries=2, retry_delay=0.1)
        
        # 3번 호출되었는지 확인 (초기 + 2번 재시도)
        self.assertEqual(mock_boto_client.call_count, 3)
    
    @patch('boto3.client')
    def test_initialize_clients(self, mock_boto_client):
        """여러 클라이언트 초기화 테스트"""
        # 각 서비스별 Mock 클라이언트 생성
        mock_s3 = Mock()
        mock_bedrock = Mock()
        mock_secrets = Mock()
        
        mock_s3.list_buckets.return_value = {'Buckets': []}
        mock_bedrock.list_foundation_models.return_value = {'modelSummaries': []}
        mock_secrets.list_secrets.return_value = {'SecretList': []}
        
        def side_effect(service_name, **kwargs):
            if service_name == 's3':
                return mock_s3
            elif service_name == 'bedrock-runtime':
                return mock_bedrock
            elif service_name == 'secretsmanager':
                return mock_secrets
            return Mock()
        
        mock_boto_client.side_effect = side_effect
        
        manager = AWSClientManager()
        
        # 기본 서비스들 초기화
        clients = manager.initialize_clients()
        
        # 모든 클라이언트가 초기화되어야 함
        self.assertIn('s3', clients)
        self.assertIn('bedrock-runtime', clients)
        self.assertIn('secretsmanager', clients)
        
        self.assertEqual(clients['s3'], mock_s3)
        self.assertEqual(clients['bedrock-runtime'], mock_bedrock)
        self.assertEqual(clients['secretsmanager'], mock_secrets)
    
    @patch('boto3.client')
    def test_health_check(self, mock_boto_client):
        """헬스체크 기능 테스트"""
        mock_s3 = Mock()
        mock_bedrock = Mock()
        
        mock_s3.list_buckets.return_value = {'Buckets': []}
        mock_bedrock.list_foundation_models.return_value = {'modelSummaries': []}
        
        def side_effect(service_name, **kwargs):
            if service_name == 's3':
                return mock_s3
            elif service_name == 'bedrock-runtime':
                return mock_bedrock
            return Mock()
        
        mock_boto_client.side_effect = side_effect
        
        manager = AWSClientManager()
        
        # 클라이언트들 초기화
        manager.get_client('s3')
        manager.get_client('bedrock-runtime')
        
        # 헬스체크 수행
        health_status = manager.health_check()
        
        # 모든 클라이언트가 정상이어야 함
        self.assertTrue(health_status['s3_us-east-1'])
        self.assertTrue(health_status['bedrock-runtime_us-east-1'])
    
    @patch('boto3.client')
    def test_health_check_failure(self, mock_boto_client):
        """헬스체크 실패 테스트"""
        mock_s3 = Mock()
        mock_s3.list_buckets.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'ListBuckets')
        
        mock_boto_client.return_value = mock_s3
        
        manager = AWSClientManager()
        
        # 클라이언트 초기화 (헬스체크는 스킵됨)
        with patch.object(manager, '_validate_client'):
            manager.get_client('s3')
        
        # 헬스체크 수행 (실패해야 함)
        health_status = manager.health_check()
        
        # S3 클라이언트가 실패해야 함
        self.assertFalse(health_status['s3_us-east-1'])
    
    def test_clear_clients(self):
        """클라이언트 캐시 초기화 테스트"""
        manager = AWSClientManager()
        
        # 가짜 클라이언트 추가
        manager._clients['test_client'] = Mock()
        
        # 캐시 초기화
        manager.clear_clients()
        
        # 캐시가 비어있어야 함
        self.assertEqual(len(manager._clients), 0)
    
    @patch('boto3.client')
    def test_get_client_info(self, mock_boto_client):
        """클라이언트 정보 조회 테스트"""
        mock_client = Mock()
        mock_client.meta.service_model.service_name = 's3'
        mock_client.meta.region_name = 'us-east-1'
        mock_client.meta.endpoint_url = 'https://s3.us-east-1.amazonaws.com'
        mock_client.meta.service_model.api_version = '2006-03-01'
        mock_client.list_buckets.return_value = {'Buckets': []}
        
        mock_boto_client.return_value = mock_client
        
        manager = AWSClientManager()
        manager.get_client('s3')
        
        # 클라이언트 정보 조회
        info = manager.get_client_info()
        
        # 정보가 올바르게 반환되어야 함
        self.assertIn('s3_us-east-1', info)
        client_info = info['s3_us-east-1']
        self.assertEqual(client_info['service_name'], 's3')
        self.assertEqual(client_info['region_name'], 'us-east-1')
    
    @patch('src.core.aws_clients.get_aws_client_manager')
    def test_get_aws_clients_wrapper(self, mock_get_manager):
        """get_aws_clients() 래퍼 함수 테스트"""
        mock_manager = Mock()
        mock_clients = {'s3': Mock(), 'bedrock-runtime': Mock()}
        mock_manager.initialize_clients.return_value = mock_clients
        mock_get_manager.return_value = mock_manager
        
        # 래퍼 함수 호출
        clients = get_aws_clients()
        
        # 올바른 결과가 반환되어야 함
        self.assertEqual(clients, mock_clients)
        mock_manager.initialize_clients.assert_called_once()


if __name__ == '__main__':
    unittest.main()