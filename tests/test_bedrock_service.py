"""
BedrockService 테스트 모듈

BedrockService의 Nova 모델 호출, 스트리밍, 토큰 사용량 로깅 등을 테스트합니다.
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from src.services.bedrock_service import BedrockService
from src.core.streaming_handler import StreamingHandler


class TestBedrockService(unittest.TestCase):
    """BedrockService 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.mock_bedrock_client = Mock()
        self.bedrock_service = BedrockService(self.mock_bedrock_client)
    
    def test_invoke_model_sync_success(self):
        """동기 모델 호출 성공 테스트"""
        # Mock 응답 설정
        mock_response_body = {
            'output': {
                'message': {
                    'content': [{'text': 'Hello, this is Nova response!'}]
                }
            },
            'usage': {
                'inputTokens': 50,
                'outputTokens': 25,
                'totalTokens': 75
            }
        }
        
        # Mock body 설정
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body)
        mock_response = Mock()
        mock_response.get.return_value = mock_body
        self.mock_bedrock_client.invoke_model.return_value = mock_response
        
        # 테스트 실행
        result = self.bedrock_service.invoke_model_sync(
            model_id='amazon.nova-micro-v1:0',
            prompt='Hello',
            max_tokens=100,
            temperature=0.3
        )
        
        # 검증
        assert result['content'] == 'Hello, this is Nova response!'
        assert result['model_id'] == 'amazon.nova-micro-v1:0'
        assert result['usage']['inputTokens'] == 50
        assert result['usage']['outputTokens'] == 25
        
        # Bedrock 클라이언트 호출 검증
        self.mock_bedrock_client.invoke_model.assert_called_once()
    
    def test_invoke_model_sync_with_caching(self):
        """캐싱을 사용한 동기 모델 호출 테스트"""
        # Mock 응답 설정
        mock_response_body = {
            'output': {
                'message': {
                    'content': [{'text': 'Cached response'}]
                }
            },
            'usage': {
                'inputTokens': 100,
                'outputTokens': 30,
                'totalTokens': 130,
                'cacheReadInputTokenCount': 80
            }
        }
        
        # Mock body 설정
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body)
        mock_response = Mock()
        mock_response.get.return_value = mock_body
        self.mock_bedrock_client.invoke_model.return_value = mock_response
        
        # 테스트 실행 (캐싱 사용)
        result = self.bedrock_service.invoke_model_sync(
            model_id='amazon.nova-pro-v1:0',
            prompt='Test with caching',
            use_caching=True
        )
        
        # 검증
        assert result['content'] == 'Cached response'
        assert result['usage']['cacheReadInputTokenCount'] == 80
        
        # 캐싱 관련 호출 검증
        call_args = self.mock_bedrock_client.invoke_model.call_args
        body = json.loads(call_args[1]['body'])
        assert 'cachePoint' in str(body['messages'][0]['content'][0])
    
    def test_invoke_model_sync_error_handling(self):
        """동기 모델 호출 오류 처리 테스트"""
        # Bedrock 클라이언트에서 예외 발생 시뮬레이션
        self.mock_bedrock_client.invoke_model.side_effect = Exception("API Error")
        
        # 테스트 실행
        result = self.bedrock_service.invoke_model_sync(
            model_id='amazon.nova-micro-v1:0',
            prompt='Test'
        )
        
        # 오류 시 빈 응답과 에러 정보 반환 검증
        assert result['content'] == ''
        assert result['model_id'] == 'amazon.nova-micro-v1:0'
        assert 'error' in result
        assert result['error'] == 'API Error'


if __name__ == '__main__':
    unittest.main()