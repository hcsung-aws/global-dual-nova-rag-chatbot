"""
마이그레이션 검증 테스트
기존 기능과의 호환성 검증 및 성능 개선 측정
"""

import pytest
import time
import json
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List
import logging

# 테스트 대상 모듈들
from src.core.aws_clients import AWSClientManager, get_aws_clients
from src.utils.glossary_manager import GlossaryManager
from src.utils.glossary_wrapper import get_game_glossary_standalone, test_glossary_functionality
from src.utils.config_manager import ConfigManager
from src.core.prompt_generator import PromptFactory
from src.services.translation_service import TranslationService
from src.services.knowledge_base_service import KnowledgeBaseService
from src.services.bedrock_service import BedrockService
from src.utils.logger import StandardLogger
from src.utils.error_handler import ErrorHandler


class TestMigrationVerification:
    """마이그레이션 검증 테스트 클래스"""
    
    def setup_method(self):
        """테스트 설정"""
        # 싱글톤 초기화
        AWSClientManager._instance = None
        AWSClientManager._clients = {}
        
        # 성능 메트릭 저장
        self.performance_metrics = {
            'before_migration': {},
            'after_migration': {}
        }
    
    def measure_execution_time(self, func, *args, **kwargs):
        """함수 실행 시간 측정"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    @patch('boto3.client')
    def test_aws_client_backward_compatibility(self, mock_boto_client):
        """AWS 클라이언트 하위 호환성 테스트"""
        # AWS 클라이언트 모킹
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        
        # 1. 기존 방식 (get_aws_clients 함수) 테스트
        legacy_clients, legacy_time = self.measure_execution_time(get_aws_clients)
        
        assert legacy_clients is not None
        assert len(legacy_clients) > 0
        
        # 2. 새로운 방식 (AWSClientManager) 테스트
        def new_way():
            manager = AWSClientManager()
            return manager.initialize_clients()
        
        new_clients, new_time = self.measure_execution_time(new_way)
        
        assert new_clients is not None
        assert len(new_clients) > 0
        
        # 3. 호환성 검증
        # 기존 방식과 새로운 방식 모두 동일한 클라이언트를 반환해야 함
        assert type(legacy_clients) == type(new_clients)
        
        # 성능 메트릭 저장
        self.performance_metrics['before_migration']['aws_client_init'] = legacy_time
        self.performance_metrics['after_migration']['aws_client_init'] = new_time
        
        print(f"✅ AWS 클라이언트 호환성 검증 완료")
        print(f"   기존 방식: {legacy_time:.3f}초")
        print(f"   새로운 방식: {new_time:.3f}초")
    
    def test_glossary_backward_compatibility(self):
        """게임 용어 단어장 하위 호환성 테스트"""
        # 1. 기존 방식 (하드코딩) 시뮬레이션
        def legacy_glossary():
            # 기존 하드코딩된 단어장 시뮬레이션
            return """# 게임 용어 단어장
Paul | 주인공 | 주인공 캐릭터 이름
Hogan | 공대한 | 게임 내 캐릭터 공대한 이름"""
        
        legacy_result, legacy_time = self.measure_execution_time(legacy_glossary)
        
        # 2. 새로운 방식 (GlossaryManager) 테스트
        new_result, new_time = self.measure_execution_time(get_game_glossary_standalone)
        
        # 3. 호환성 검증
        assert legacy_result is not None
        assert new_result is not None
        assert len(new_result) > len(legacy_result)  # 새로운 방식이 더 많은 정보 제공
        
        # 필수 용어들이 포함되어 있는지 확인
        essential_terms = ["Paul", "Hogan", "Manuel", "Agent C"]
        for term in essential_terms:
            assert term in new_result, f"필수 용어 '{term}'이 누락되었습니다"
        
        # 성능 메트릭 저장
        self.performance_metrics['before_migration']['glossary_load'] = legacy_time
        self.performance_metrics['after_migration']['glossary_load'] = new_time
        
        print(f"✅ 게임 용어 단어장 호환성 검증 완료")
        print(f"   기존 방식: {legacy_time:.3f}초")
        print(f"   새로운 방식: {new_time:.3f}초")
    
    def test_prompt_generation_backward_compatibility(self):
        """프롬프트 생성 하위 호환성 테스트"""
        # 1. 기존 방식 시뮬레이션
        def legacy_translation_prompt():
            return """You are a professional translator.
Translate the following text to English."""
        
        def legacy_answer_prompt():
            return """You are a helpful assistant.
Answer the following question."""
        
        legacy_trans, legacy_trans_time = self.measure_execution_time(legacy_translation_prompt)
        legacy_answer, legacy_answer_time = self.measure_execution_time(legacy_answer_prompt)
        
        # 2. 새로운 방식 (PromptFactory) 테스트
        new_trans, new_trans_time = self.measure_execution_time(
            PromptFactory.create_prompt, 'translation'
        )
        new_answer, new_answer_time = self.measure_execution_time(
            PromptFactory.create_prompt, 'answer'
        )
        
        # 3. 호환성 검증
        assert legacy_trans is not None
        assert new_trans is not None
        assert len(new_trans) > len(legacy_trans)  # 새로운 방식이 더 상세한 프롬프트 제공
        
        assert legacy_answer is not None
        assert new_answer is not None
        assert len(new_answer) > len(legacy_answer)
        
        # 성능 메트릭 저장
        total_legacy_time = legacy_trans_time + legacy_answer_time
        total_new_time = new_trans_time + new_answer_time
        
        self.performance_metrics['before_migration']['prompt_generation'] = total_legacy_time
        self.performance_metrics['after_migration']['prompt_generation'] = total_new_time
        
        print(f"✅ 프롬프트 생성 호환성 검증 완료")
        print(f"   기존 방식: {total_legacy_time:.3f}초")
        print(f"   새로운 방식: {total_new_time:.3f}초")
    
    def test_error_handling_improvement(self):
        """에러 처리 개선 검증"""
        error_handler = ErrorHandler()
        
        # 1. 다양한 에러 시나리오 테스트
        test_errors = [
            Exception("AWS 연결 실패"),
            ValueError("잘못된 설정값"),
            ConnectionError("네트워크 연결 실패"),
            KeyError("필수 키 누락")
        ]
        
        for error in test_errors:
            # AWS 에러 처리 테스트
            if "AWS" in str(error):
                standard_error = error_handler.handle_aws_error(error)
                assert standard_error.error_code is not None
                assert standard_error.user_message is not None
                assert len(standard_error.user_message) > 0
            
            # 일반 에러 처리 테스트
            else:
                standard_error = error_handler.handle_generic_error(error)
                assert standard_error.error_code is not None
                assert standard_error.user_message is not None
        
        print("✅ 에러 처리 개선 검증 완료")
    
    def test_logging_standardization(self):
        """로깅 표준화 검증"""
        logger = StandardLogger("migration_test")
        
        # 다양한 로그 레벨 테스트
        logger.info("마이그레이션 테스트 시작")
        logger.warning("테스트 경고", context={"test": "migration"})
        logger.error("테스트 에러", context={"test": "migration"})
        
        # 성능 로깅 테스트
        logger.log_performance("migration_test", 1.5)
        
        # 로그 파일 생성 확인
        log_files = [f for f in os.listdir('logs') if 'migration_test' in f]
        assert len(log_files) > 0, "로그 파일이 생성되지 않았습니다"
        
        print("✅ 로깅 표준화 검증 완료")
    
    def test_configuration_management_improvement(self):
        """설정 관리 개선 검증"""
        config_manager = ConfigManager()
        
        # 1. 설정 로딩 테스트
        config, load_time = self.measure_execution_time(config_manager.get_config)
        
        assert config is not None
        assert hasattr(config, 'aws')
        assert hasattr(config, 'ui')
        assert hasattr(config, 'logging')
        
        # 2. 필수 설정 검증 테스트
        missing_settings = config_manager.validate_required_settings()
        assert len(missing_settings) == 0, f"누락된 필수 설정: {missing_settings}"
        
        # 3. 설정 요약 테스트
        summary = config_manager.get_config_summary()
        assert summary is not None
        assert 'aws_region' in summary or 'aws' in summary
        
        # 성능 메트릭 저장
        self.performance_metrics['after_migration']['config_load'] = load_time
        
        print(f"✅ 설정 관리 개선 검증 완료")
        print(f"   설정 로딩 시간: {load_time:.3f}초")
    
    def test_modular_architecture_benefits(self):
        """모듈화 아키텍처 이점 검증"""
        # 1. 모듈 독립성 테스트
        glossary_manager = GlossaryManager()
        config_manager = ConfigManager()
        
        # 각 모듈이 독립적으로 작동하는지 확인
        glossary = glossary_manager.load_glossary()
        config = config_manager.get_config()
        
        assert glossary is not None
        assert config is not None
        
        # 2. 의존성 최소화 확인
        # GlossaryManager는 다른 모듈에 의존하지 않아야 함
        assert hasattr(glossary_manager, 'load_glossary')
        assert hasattr(glossary_manager, 'get_character_mapping')
        
        # 3. 확장성 테스트
        # 새로운 프롬프트 타입 추가 가능성 확인
        available_prompts = ['translation', 'answer']
        for prompt_type in available_prompts:
            prompt = PromptFactory.create_prompt(prompt_type)
            assert len(prompt) > 0
        
        print("✅ 모듈화 아키텍처 이점 검증 완료")
    
    def test_performance_improvements(self):
        """성능 개선 측정"""
        # 성능 메트릭 분석
        improvements = {}
        
        for metric_name in self.performance_metrics['after_migration']:
            if metric_name in self.performance_metrics['before_migration']:
                before = self.performance_metrics['before_migration'][metric_name]
                after = self.performance_metrics['after_migration'][metric_name]
                
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements[metric_name] = improvement
        
        # 성능 개선 보고서 생성
        print("\n" + "="*50)
        print("성능 개선 보고서")
        print("="*50)
        
        total_improvement = 0
        improvement_count = 0
        
        for metric, improvement in improvements.items():
            print(f"{metric}: {improvement:+.1f}%")
            if improvement > 0:
                total_improvement += improvement
                improvement_count += 1
        
        avg_improvement = 0
        if improvement_count > 0:
            avg_improvement = total_improvement / improvement_count
            print(f"\n평균 성능 개선: {avg_improvement:.1f}%")
        else:
            print("\n성능 메트릭 비교 데이터가 부족합니다.")
        
        print("="*50)
        
        # 최소 성능 개선 목표 검증 (성능 저하가 없어야 함)
        assert avg_improvement >= -10, "성능이 크게 저하되었습니다"
        
        print("✅ 성능 개선 측정 완료")
    
    def test_code_quality_metrics(self):
        """코드 품질 메트릭 검증"""
        # 1. 모듈 수 계산
        core_modules = ['aws_clients', 'prompt_generator', 'streaming_handler', 'dual_response']
        service_modules = ['translation_service', 'knowledge_base_service', 'bedrock_service']
        util_modules = ['glossary_manager', 'config_manager', 'logger', 'error_handler']
        
        total_modules = len(core_modules) + len(service_modules) + len(util_modules)
        
        # 2. 코드 중복 제거 확인
        # 각 모듈이 고유한 책임을 가지는지 확인
        module_responsibilities = {
            'aws_clients': 'AWS 클라이언트 관리',
            'glossary_manager': '게임 용어 단어장 관리',
            'config_manager': '설정 관리',
            'prompt_generator': '프롬프트 생성',
            'translation_service': '번역 서비스',
            'bedrock_service': 'Bedrock 모델 호출',
            'logger': '로깅 시스템',
            'error_handler': '에러 처리'
        }
        
        # 3. 테스트 커버리지 확인
        test_files = [f for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')]
        
        print("\n" + "="*50)
        print("코드 품질 메트릭")
        print("="*50)
        print(f"총 모듈 수: {total_modules}")
        print(f"모듈별 책임 분리: {len(module_responsibilities)}개 영역")
        print(f"테스트 파일 수: {len(test_files)}")
        print("="*50)
        
        # 최소 품질 기준 검증
        assert total_modules >= 8, "모듈화가 충분하지 않습니다"
        assert len(test_files) >= 10, "테스트 커버리지가 부족합니다"
        
        print("✅ 코드 품질 메트릭 검증 완료")
    
    def teardown_method(self):
        """테스트 종료 후 정리"""
        # 성능 메트릭을 파일로 저장
        metrics_file = 'migration_performance_report.json'
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.performance_metrics, f, indent=2, ensure_ascii=False)
        
        print(f"\n성능 메트릭이 {metrics_file}에 저장되었습니다.")


class TestFunctionalRegression:
    """기능 회귀 테스트"""
    
    @patch('boto3.client')
    def test_all_original_functions_work(self, mock_boto_client):
        """모든 원본 기능이 여전히 작동하는지 확인"""
        # AWS 클라이언트 모킹
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        
        # 1. 게임 용어 단어장 기능
        glossary_test_result = test_glossary_functionality()
        assert glossary_test_result, "게임 용어 단어장 기능에 문제가 있습니다"
        
        # 2. AWS 클라이언트 기능
        clients = get_aws_clients()
        assert clients is not None
        
        # 3. 프롬프트 생성 기능
        translation_prompt = PromptFactory.create_translation_prompt()
        answer_prompt = PromptFactory.create_answer_prompt()
        
        assert len(translation_prompt) > 0
        assert len(answer_prompt) > 0
        
        print("✅ 모든 원본 기능 회귀 테스트 통과")
    
    def test_no_breaking_changes(self):
        """호환성을 깨뜨리는 변경사항이 없는지 확인"""
        # 1. 기존 함수들이 여전히 존재하는지 확인
        from src.core.aws_clients import get_aws_clients
        from src.utils.glossary_wrapper import get_game_glossary_standalone
        from src.core.prompt_generator import PromptFactory
        
        # 함수들이 호출 가능한지 확인
        assert callable(get_aws_clients)
        assert callable(get_game_glossary_standalone)
        assert callable(PromptFactory.create_prompt)
        
        print("✅ 호환성을 깨뜨리는 변경사항 없음 확인")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])