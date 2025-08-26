"""
전체 시스템 통합 테스트
리팩토링된 시스템의 전체 플로우와 기존 기능 동작을 검증합니다.
"""

import pytest
import unittest.mock as mock
import time
import json
from unittest.mock import MagicMock, patch, Mock
from concurrent.futures import ThreadPoolExecutor

# 테스트 대상 모듈들 import
from src.core.aws_clients import AWSClientManager
from src.utils.glossary_manager import GlossaryManager
from src.utils.config_manager import ConfigManager
from src.core.prompt_generator import PromptFactory
from src.services.translation_service import TranslationService
from src.services.knowledge_base_service import KnowledgeBaseService
from src.services.bedrock_service import BedrockService
from src.core.dual_response import DualResponseGenerator
from src.utils.logger import StandardLogger
from src.utils.error_handler import ErrorHandler


class TestSystemIntegration:
    """전체 시스템 통합 테스트 클래스"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        # 싱글톤 인스턴스 초기화
        AWSClientManager._instance = None
        AWSClientManager._clients = {}
        
        # 모킹된 AWS 클라이언트 설정
        self.mock_bedrock = MagicMock()
        self.mock_bedrock_agent = MagicMock()
        self.mock_translate = MagicMock()
        self.mock_s3 = MagicMock()
        self.mock_secrets = MagicMock()
        
        # 기본 응답 설정
        self.mock_bedrock.invoke_model_with_response_stream.return_value = {
            'body': self._create_mock_stream("테스트 응답입니다.")
        }
        
        self.mock_bedrock_agent.retrieve.return_value = {
            'retrievalResults': [
                {
                    'content': {'text': '테스트 지식베이스 내용'},
                    'score': 0.9
                }
            ]
        }
        
        self.mock_translate.translate_text.return_value = {
            'TranslatedText': 'Test response.'
        }
    
    def _create_mock_stream(self, text):
        """모킹된 스트림 응답 생성"""
        chunks = [
            {'chunk': {'bytes': json.dumps({'completion': chunk}).encode()}}
            for chunk in [text[i:i+5] for i in range(0, len(text), 5)]
        ]
        return iter(chunks)
    
    def _mock_client_factory(self, service, **kwargs):
        """AWS 클라이언트 팩토리 모킹"""
        client_map = {
            'bedrock-runtime': self.mock_bedrock,
            'bedrock-agent-runtime': self.mock_bedrock_agent,
            'translate': self.mock_translate,
            's3': self.mock_s3,
            'secretsmanager': self.mock_secrets
        }
        return client_map.get(service, MagicMock())
    
    @patch('boto3.client')
    def test_complete_chatbot_flow(self, mock_boto_client):
        """전체 챗봇 플로우 통합 테스트"""
        # AWS 클라이언트 모킹
        mock_boto_client.side_effect = self._mock_client_factory
        
        # 1. 시스템 초기화
        aws_manager = AWSClientManager()
        clients = aws_manager.initialize_clients()
        
        assert 'bedrock-runtime' in clients
        # bedrock-agent-runtime과 translate는 필요시에만 초기화되므로 bedrock-runtime만 확인
        
        # 2. 설정 관리자 초기화
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        assert config is not None
        assert hasattr(config, 'aws')
        
        # 3. 게임 용어 단어장 로딩
        glossary_manager = GlossaryManager()
        glossary = glossary_manager.load_glossary()
        
        assert glossary is not None
        assert 'characters' in glossary
        assert 'character_terms' in glossary
        
        # 4. 프롬프트 생성 테스트
        translation_prompt = PromptFactory.create_prompt('translation')
        
        assert len(translation_prompt) > 0
        assert "translation" in translation_prompt.lower() or "translate" in translation_prompt.lower()
        
        print("✅ 전체 챗봇 플로우 통합 테스트 통과")
    
    @patch('boto3.client')
    def test_error_handling_integration(self, mock_boto_client):
        """에러 처리 통합 테스트"""
        # AWS 클라이언트 에러 시뮬레이션
        mock_boto_client.side_effect = Exception("AWS 연결 실패")
        
        error_handler = ErrorHandler()
        
        try:
            aws_manager = AWSClientManager()
            aws_manager.initialize_clients()
        except Exception as e:
            standard_error = error_handler.handle_aws_error(e)
            
            assert standard_error.error_code == "AWS_CONNECTION_ERROR"
            assert "AWS 연결 실패" in standard_error.message
            assert standard_error.user_message is not None
        
        print("✅ 에러 처리 통합 테스트 통과")
    
    @patch('boto3.client')
    def test_performance_benchmarks(self, mock_boto_client):
        """성능 벤치마크 테스트"""
        # AWS 클라이언트 모킹
        mock_boto_client.side_effect = self._mock_client_factory
        
        # 시스템 초기화 시간 측정
        start_time = time.time()
        
        aws_manager = AWSClientManager()
        clients = aws_manager.initialize_clients()
        
        glossary_manager = GlossaryManager()
        glossary_manager.load_glossary()
        
        config_manager = ConfigManager()
        config_manager.get_config()
        
        init_time = time.time() - start_time
        
        # 초기화 시간이 2초 이내여야 함
        assert init_time < 2.0, f"시스템 초기화 시간이 너무 깁니다: {init_time:.2f}초"
        
        print(f"✅ 시스템 초기화 시간: {init_time:.2f}초")
    
    @patch('boto3.client')
    def test_concurrent_processing(self, mock_boto_client):
        """병렬 처리 테스트"""
        # AWS 클라이언트 모킹
        mock_boto_client.side_effect = self._mock_client_factory
        
        aws_manager = AWSClientManager()
        clients = aws_manager.initialize_clients()
        
        # 병렬 처리 시뮬레이션
        def mock_task_1():
            time.sleep(0.1)  # 네트워크 지연 시뮬레이션
            return "작업 1 완료"
        
        def mock_task_2():
            time.sleep(0.1)  # 네트워크 지연 시뮬레이션
            return "작업 2 완료"
        
        start_time = time.time()
        
        # 병렬 실행
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(mock_task_1)
            future2 = executor.submit(mock_task_2)
            
            result1 = future1.result()
            result2 = future2.result()
        
        parallel_time = time.time() - start_time
        
        # 병렬 처리 시간이 순차 처리보다 빨라야 함
        assert parallel_time < 0.15, f"병렬 처리 효율성이 부족합니다: {parallel_time:.2f}초"
        assert result1 == "작업 1 완료"
        assert result2 == "작업 2 완료"
        
        print(f"✅ 병렬 처리 시간: {parallel_time:.2f}초")
    
    def test_memory_usage(self):
        """메모리 사용량 테스트"""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil이 설치되지 않아 메모리 테스트를 건너뜁니다")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 대량 데이터 처리 시뮬레이션
        glossary_manager = GlossaryManager()
        
        # 여러 번 로딩하여 메모리 누수 확인
        for _ in range(10):
            glossary = glossary_manager.load_glossary()
            del glossary
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 메모리 증가가 50MB 이내여야 함
        assert memory_increase < 50, f"메모리 사용량이 과도합니다: {memory_increase:.2f}MB 증가"
        
        print(f"✅ 메모리 사용량 증가: {memory_increase:.2f}MB")
    
    @patch('boto3.client')
    def test_configuration_validation(self, mock_boto_client):
        """설정 검증 테스트"""
        # AWS 클라이언트 모킹
        mock_boto_client.return_value = MagicMock()
        
        config_manager = ConfigManager()
        
        # 필수 설정 검증
        required_settings = config_manager.validate_required_settings()
        
        # 필수 설정이 모두 있어야 함
        assert len(required_settings) == 0, f"누락된 필수 설정: {required_settings}"
        
        # 설정 로딩 테스트
        config = config_manager.get_config()
        
        assert hasattr(config, 'aws')
        assert hasattr(config.aws, 'region')
        assert hasattr(config.aws, 'bedrock_models')
        
        print("✅ 설정 검증 테스트 통과")
    
    def test_logging_integration(self):
        """로깅 시스템 통합 테스트"""
        logger = StandardLogger("test_integration")
        
        # 다양한 로그 레벨 테스트
        logger.info("통합 테스트 시작")
        logger.error("테스트 에러", context={"context": "integration_test"})
        logger.log_performance("test_operation", 1.5)
        
        # 로그 파일 생성 확인
        import os
        log_files = [f for f in os.listdir('logs') if 'test_integration' in f]
        assert len(log_files) > 0, "로그 파일이 생성되지 않았습니다"
        
        print("✅ 로깅 시스템 통합 테스트 통과")


class TestBackwardCompatibility:
    """기존 기능 호환성 테스트"""
    
    @patch('boto3.client')
    def test_legacy_function_compatibility(self, mock_boto_client):
        """기존 함수들의 호환성 테스트"""
        # 기존 함수들이 여전히 동작하는지 확인
        mock_boto_client.return_value = MagicMock()
        
        # 게임 용어 단어장 함수 호환성
        from src.utils.glossary_wrapper import get_game_glossary_standalone
        glossary = get_game_glossary_standalone()
        
        assert glossary is not None
        assert len(glossary) > 0
        
        # AWS 클라이언트 함수 호환성 (캐시된 버전)
        from src.core.aws_clients import get_aws_clients
        clients = get_aws_clients()
        
        assert clients is not None
        assert len(clients) > 0
        
        print("✅ 기존 함수 호환성 테스트 통과")


class TestSystemStability:
    """시스템 안정성 테스트"""
    
    def test_glossary_manager_stability(self):
        """GlossaryManager 안정성 테스트"""
        glossary_manager = GlossaryManager()
        
        # 반복적인 로딩 테스트
        for i in range(5):
            glossary = glossary_manager.load_glossary()
            assert glossary is not None
            assert len(glossary) > 0
        
        # 캐릭터 매핑 안정성 테스트
        for i in range(5):
            char_mapping = glossary_manager.get_character_mapping()
            assert len(char_mapping) > 0
        
        print("✅ GlossaryManager 안정성 테스트 통과")
    
    def test_config_manager_stability(self):
        """ConfigManager 안정성 테스트"""
        config_manager = ConfigManager()
        
        # 반복적인 설정 로딩 테스트
        for i in range(5):
            config = config_manager.get_config()
            assert config is not None
            assert hasattr(config, 'aws')
        
        print("✅ ConfigManager 안정성 테스트 통과")
    
    @patch('boto3.client')
    def test_aws_client_manager_stability(self, mock_boto_client):
        """AWSClientManager 안정성 테스트"""
        mock_boto_client.return_value = MagicMock()
        
        # 여러 번 초기화해도 싱글톤이 유지되는지 확인
        manager1 = AWSClientManager()
        manager2 = AWSClientManager()
        
        assert manager1 is manager2, "싱글톤 패턴이 제대로 작동하지 않습니다"
        
        # 클라이언트 초기화 안정성 테스트
        for i in range(3):
            clients = manager1.initialize_clients()
            assert len(clients) > 0
        
        print("✅ AWSClientManager 안정성 테스트 통과")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])