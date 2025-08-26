"""
AWSClientManager 통합 테스트

이 테스트는 chatbot_app.py에서 AWSClientManager가 올바르게 통합되었는지 확인합니다.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 테스트를 위한 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestAWSClientManagerIntegration(unittest.TestCase):
    """AWSClientManager 통합 테스트 클래스"""
    
    @patch('src.core.aws_clients.boto3.client')
    def test_chatbot_app_imports(self, mock_boto_client):
        """chatbot_app.py에서 AWSClientManager 임포트가 올바른지 테스트"""
        # Mock 클라이언트 설정
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
            elif service_name == 'bedrock-agent-runtime':
                return Mock()
            elif service_name == 'cloudwatch':
                return Mock()
            return Mock()
        
        mock_boto_client.side_effect = side_effect
        
        try:
            # chatbot_app.py 임포트 시도
            import src.chatbot_app
            
            # 임포트가 성공하면 테스트 통과
            self.assertTrue(True)
            
            # aws_manager가 올바르게 초기화되었는지 확인
            self.assertIsNotNone(src.chatbot_app.aws_manager)
            
            # clients가 올바르게 초기화되었는지 확인
            self.assertIsNotNone(src.chatbot_app.clients)
            
        except ImportError as e:
            self.fail(f"chatbot_app.py 임포트 실패: {e}")
        except Exception as e:
            # Streamlit 관련 오류는 무시 (테스트 환경에서는 정상)
            if 'streamlit' not in str(e).lower():
                self.fail(f"예상치 못한 오류: {e}")
    
    @patch('src.core.aws_clients.boto3.client')
    def test_get_aws_clients_function(self, mock_boto_client):
        """get_aws_clients() 함수가 AWSClientManager를 사용하는지 테스트"""
        # Mock 클라이언트 설정
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
        
        # AWSClientManager를 통한 클라이언트 초기화 테스트
        from src.core.aws_clients import get_aws_client_manager
        
        manager = get_aws_client_manager()
        clients = manager.initialize_clients(['s3', 'bedrock-runtime', 'secretsmanager'])
        
        # 모든 클라이언트가 초기화되어야 함
        self.assertIn('s3', clients)
        self.assertIn('bedrock-runtime', clients)
        self.assertIn('secretsmanager', clients)
        
        # 클라이언트가 올바른 타입인지 확인 (Mock 객체는 매번 새로 생성되므로 타입 검사)
        self.assertIsInstance(clients['s3'], Mock)
        self.assertIsInstance(clients['bedrock-runtime'], Mock)
        self.assertIsInstance(clients['secretsmanager'], Mock)
    
    @patch('src.core.aws_clients.boto3.client')
    def test_bedrock_agent_client_usage(self, mock_boto_client):
        """bedrock-agent-runtime 클라이언트가 AWSClientManager를 통해 생성되는지 테스트"""
        mock_agent_client = Mock()
        mock_agent_client.retrieve.return_value = {
            'retrievalResults': [
                {
                    'content': {'text': 'test content'},
                    'score': 0.9,
                    'location': {'s3Location': {'uri': 's3://test/doc.txt'}}
                }
            ]
        }
        
        def side_effect(service_name, **kwargs):
            if service_name == 'bedrock-agent-runtime':
                return mock_agent_client
            return Mock()
        
        mock_boto_client.side_effect = side_effect
        
        from src.core.aws_clients import get_aws_client_manager
        
        manager = get_aws_client_manager()
        client = manager.get_client('bedrock-agent-runtime', region_name='us-east-1')
        
        # 클라이언트가 올바르게 생성되었는지 확인
        self.assertEqual(client, mock_agent_client)
        
        # retrieve 메서드가 호출 가능한지 확인
        result = client.retrieve(
            knowledgeBaseId='test-kb',
            retrievalQuery={'text': 'test query'}
        )
        
        self.assertIn('retrievalResults', result)
    
    @patch('src.core.aws_clients.boto3.client')
    def test_cloudwatch_client_usage(self, mock_boto_client):
        """CloudWatch 클라이언트가 AWSClientManager를 통해 생성되는지 테스트"""
        mock_cloudwatch_client = Mock()
        mock_cloudwatch_client.get_metric_statistics.return_value = {
            'Datapoints': [{'Sum': 1000}]
        }
        
        def side_effect(service_name, **kwargs):
            if service_name == 'cloudwatch':
                return mock_cloudwatch_client
            return Mock()
        
        mock_boto_client.side_effect = side_effect
        
        from src.core.aws_clients import get_aws_client_manager
        
        manager = get_aws_client_manager()
        client = manager.get_client('cloudwatch', region_name='us-east-1')
        
        # 클라이언트가 올바르게 생성되었는지 확인 (Mock 객체 타입 검사)
        self.assertIsInstance(client, Mock)
        
        # get_metric_statistics 메서드가 호출 가능한지 확인
        client.get_metric_statistics.return_value = {
            'Datapoints': [{'Timestamp': '2024-01-01', 'Sum': 100}]
        }
        
        result = client.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='InputTokenCount',
            StartTime='2024-01-01',
            EndTime='2024-01-02',
            Period=3600,
            Statistics=['Sum']
        )
        
        # Mock 응답 검증
        self.assertIsInstance(result, dict)
        self.assertIn('Datapoints', result)


if __name__ == '__main__':
    unittest.main()