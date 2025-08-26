"""
TranslationService 단위 테스트

번역 서비스의 핵심 기능을 검증합니다.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.services.translation_service import TranslationService


class TestTranslationService:
    """TranslationService 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_aws_manager = Mock()
        self.mock_bedrock_client = Mock()
        self.mock_aws_manager.get_client.return_value = self.mock_bedrock_client
        
        self.translation_service = TranslationService(self.mock_aws_manager)
    
    def test_detect_language_korean(self):
        """한국어 텍스트 언어 감지 테스트"""
        korean_text = "안녕하세요"
        result = self.translation_service._detect_language(korean_text)
        assert result == "Korean"
    
    def test_detect_language_english(self):
        """영어 텍스트 언어 감지 테스트"""
        english_text = "Hello World"
        result = self.translation_service._detect_language(english_text)
        assert result == "English"
    
    def test_detect_language_mixed(self):
        """한영 혼합 텍스트 언어 감지 테스트 (한글 우선)"""
        mixed_text = "Hello 안녕하세요"
        result = self.translation_service._detect_language(mixed_text)
        assert result == "Korean"
    
    @patch('src.services.translation_service.PromptFactory')
    def test_translate_text_with_caching_success(self, mock_prompt_factory):
        """번역 성공 케이스 테스트"""
        # Mock 설정
        mock_prompt_factory.create_translation_prompt.return_value = "Mock translation prompt"
        
        mock_response = Mock()
        mock_response_body = {
            'output': {
                'message': {
                    'content': [{'text': 'Hello World'}]
                }
            },
            'usage': {
                'inputTokens': 100,
                'outputTokens': 50,
                'totalTokens': 150,
                'cacheReadInputTokenCount': 80,
                'cacheWriteInputTokenCount': 20
            }
        }
        mock_response.get.return_value.read.return_value = json.dumps(mock_response_body)
        self.mock_bedrock_client.invoke_model.return_value = mock_response
        
        # 테스트 실행
        result = self.translation_service.translate_text_with_caching("안녕하세요", "English")
        
        # 검증
        assert result["original_text"] == "안녕하세요"
        assert result["detected_language"] == "Korean"
        assert result["target_language"] == "English"
        assert result["translated_text"] == "Hello World"
        
        # Bedrock 클라이언트 호출 검증
        self.mock_bedrock_client.invoke_model.assert_called_once()
        call_args = self.mock_bedrock_client.invoke_model.call_args
        assert call_args[1]['modelId'] == 'amazon.nova-pro-v1:0'
    
    @patch('src.services.translation_service.PromptFactory')
    def test_translate_text_with_caching_auto_language(self, mock_prompt_factory):
        """자동 언어 감지 번역 테스트"""
        # Mock 설정
        mock_prompt_factory.create_translation_prompt.return_value = "Mock translation prompt"
        
        mock_response = Mock()
        mock_response_body = {
            'output': {
                'message': {
                    'content': [{'text': 'Hello World'}]
                }
            },
            'usage': {'inputTokens': 100, 'outputTokens': 50, 'totalTokens': 150}
        }
        mock_response.get.return_value.read.return_value = json.dumps(mock_response_body)
        self.mock_bedrock_client.invoke_model.return_value = mock_response
        
        # 테스트 실행 (한국어 → 영어 자동 감지)
        result = self.translation_service.translate_text_with_caching("안녕하세요", "auto")
        
        # 검증
        assert result["detected_language"] == "Korean"
        assert result["target_language"] == "English"
        assert result["translated_text"] == "Hello World"
    
    def test_translate_text_with_caching_error_handling(self):
        """번역 API 오류 처리 테스트"""
        # Bedrock 클라이언트에서 예외 발생 시뮬레이션
        self.mock_bedrock_client.invoke_model.side_effect = Exception("API Error")
        
        # 테스트 실행
        result = self.translation_service.translate_text_with_caching("안녕하세요", "English")
        
        # 오류 시 원본 텍스트 반환 검증
        assert result["original_text"] == "안녕하세요"
        assert result["translated_text"] == "안녕하세요"
        assert result["detected_language"] == "Korean"
        assert result["target_language"] == "English"
    
    @patch('src.services.translation_service.PromptFactory')
    def test_translate_text_empty_response(self, mock_prompt_factory):
        """빈 번역 결과 처리 테스트"""
        # Mock 설정
        mock_prompt_factory.create_translation_prompt.return_value = "Mock translation prompt"
        
        mock_response = Mock()
        mock_response_body = {
            'output': {
                'message': {
                    'content': [{'text': ''}]  # 빈 응답
                }
            },
            'usage': {'inputTokens': 100, 'outputTokens': 0, 'totalTokens': 100}
        }
        mock_response.get.return_value.read.return_value = json.dumps(mock_response_body)
        self.mock_bedrock_client.invoke_model.return_value = mock_response
        
        # 테스트 실행
        result = self.translation_service.translate_text_with_caching("안녕하세요", "English")
        
        # 빈 응답 시 원본 텍스트 반환 검증
        assert result["translated_text"] == "안녕하세요"
    
    def test_translate_to_korean(self):
        """한국어 번역 편의 메서드 테스트"""
        with patch.object(self.translation_service, 'translate_text_with_caching') as mock_translate:
            mock_translate.return_value = {"translated_text": "안녕하세요"}
            
            result = self.translation_service.translate_to_korean("Hello")
            
            mock_translate.assert_called_once_with("Hello", "Korean")
            assert result["translated_text"] == "안녕하세요"
    
    def test_translate_to_english(self):
        """영어 번역 편의 메서드 테스트"""
        with patch.object(self.translation_service, 'translate_text_with_caching') as mock_translate:
            mock_translate.return_value = {"translated_text": "Hello"}
            
            result = self.translation_service.translate_to_english("안녕하세요")
            
            mock_translate.assert_called_once_with("안녕하세요", "English")
            assert result["translated_text"] == "Hello"
    
    def test_get_translation_only(self):
        """번역 텍스트만 반환하는 편의 메서드 테스트"""
        with patch.object(self.translation_service, 'translate_text_with_caching') as mock_translate:
            mock_translate.return_value = {
                "original_text": "안녕하세요",
                "translated_text": "Hello",
                "detected_language": "Korean",
                "target_language": "English"
            }
            
            result = self.translation_service.get_translation_only("안녕하세요", "English")
            
            mock_translate.assert_called_once_with("안녕하세요", "English")
            assert result == "Hello"
    
    def test_log_token_usage(self):
        """토큰 사용량 로깅 테스트"""
        response_body = {
            'usage': {
                'inputTokens': 100,
                'outputTokens': 50,
                'totalTokens': 150,
                'cacheReadInputTokenCount': 80,
                'cacheWriteInputTokenCount': 20
            }
        }
        
        # 로깅 함수가 예외 없이 실행되는지 확인
        try:
            self.translation_service._log_token_usage('amazon.nova-pro-v1:0', response_body, "테스트")
        except Exception as e:
            pytest.fail(f"토큰 사용량 로깅에서 예외 발생: {e}")
    
    def test_log_token_usage_with_logger(self):
        """로거가 있는 경우 토큰 사용량 로깅 테스트"""
        mock_logger = Mock()
        self.translation_service.logger = mock_logger
        
        response_body = {
            'usage': {
                'inputTokens': 100,
                'outputTokens': 50,
                'totalTokens': 150,
                'cacheReadInputTokenCount': 80,
                'cacheWriteInputTokenCount': 20
            }
        }
        
        self.translation_service._log_token_usage('amazon.nova-pro-v1:0', response_body, "테스트")
        
        # 로거의 log_model_usage 메서드가 호출되었는지 확인
        mock_logger.log_model_usage.assert_called_once()
        call_args = mock_logger.log_model_usage.call_args[0]
        assert call_args[0] == 'amazon.nova-pro-v1:0'
        assert call_args[1]['input_tokens'] == 100
        assert call_args[1]['output_tokens'] == 50


if __name__ == "__main__":
    pytest.main([__file__])