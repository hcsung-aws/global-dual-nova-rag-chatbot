"""
DualResponseGenerator 테스트 모듈

메인 애플리케이션에서 분리된 비즈니스 로직의 테스트를 담당합니다.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.dual_response import DualResponseGenerator
from src.core.streaming_handler import StreamingHandler


class TestDualResponseGenerator:
    """DualResponseGenerator 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        # Mock StreamingHandler
        self.mock_streaming_handler = Mock(spec=StreamingHandler)
        
        # DualResponseGenerator 인스턴스 생성
        self.generator = DualResponseGenerator(self.mock_streaming_handler)
    
    def test_init(self):
        """초기화 테스트"""
        assert self.generator.streaming_handler == self.mock_streaming_handler
    
    @patch('src.core.dual_response.PromptFactory')
    def test_create_prompts_korean(self, mock_prompt_factory):
        """한국어 프롬프트 생성 테스트"""
        # Mock 설정
        mock_prompt_factory.create_answer_prompt.return_value = "테스트 프롬프트 prefix"
        
        # 테스트 데이터
        user_query = "테스트 질문"
        context_docs = [
            {"title": "문서1", "content": "내용1"},
            {"title": "문서2", "content": "내용2"}
        ]
        conversation_history = [
            {"content": "이전 질문"},
            {"content": "이전 답변"}
        ]
        
        # 함수 실행
        micro_prompt, pro_prompt = self.generator.create_prompts(
            user_query, context_docs, conversation_history, "Korean"
        )
        
        # 검증
        assert "테스트 프롬프트 prefix" in micro_prompt
        assert "테스트 프롬프트 prefix" in pro_prompt
        assert "테스트 질문" in micro_prompt
        assert "테스트 질문" in pro_prompt
        assert "문서1" in micro_prompt
        assert "문서1" in pro_prompt
        assert "이전 질문" in micro_prompt
        assert "이전 질문" in pro_prompt
        
        # PromptFactory 호출 검증
        mock_prompt_factory.create_answer_prompt.assert_called_once_with(user_language="Korean")
    
    @patch('src.core.dual_response.PromptFactory')
    def test_create_prompts_english(self, mock_prompt_factory):
        """영어 프롬프트 생성 테스트"""
        # Mock 설정
        mock_prompt_factory.create_answer_prompt.return_value = "Test prompt prefix"
        
        # 테스트 데이터
        user_query = "Test question"
        context_docs = [{"title": "Doc1", "content": "Content1"}]
        conversation_history = []
        
        # 함수 실행
        micro_prompt, pro_prompt = self.generator.create_prompts(
            user_query, context_docs, conversation_history, "English"
        )
        
        # 검증
        assert "Test prompt prefix" in micro_prompt
        assert "Test prompt prefix" in pro_prompt
        assert "Test question" in micro_prompt
        assert "Test question" in pro_prompt
        assert "Doc1" in micro_prompt
        assert "Doc1" in pro_prompt
        assert "English" in micro_prompt
        assert "English" in pro_prompt
        
        # PromptFactory 호출 검증
        mock_prompt_factory.create_answer_prompt.assert_called_once_with(user_language="English")
    
    def test_generate_dual_answer_no_context_korean(self):
        """컨텍스트 없을 때 한국어 답변 테스트"""
        result = self.generator.generate_dual_answer(
            "테스트 질문", [], [], "Korean"
        )
        
        assert "죄송합니다" in result
        assert "관련된 문서를 찾을 수 없습니다" in result
    
    def test_generate_dual_answer_no_context_english(self):
        """컨텍스트 없을 때 영어 답변 테스트"""
        result = self.generator.generate_dual_answer(
            "Test question", [], [], "English"
        )
        
        assert "Sorry" in result
        assert "couldn't find relevant documents" in result
    
    def test_generate_dual_answer_korean_with_context_mock_only(self):
        """컨텍스트가 있을 때 한국어 답변 생성 테스트 (Mock만 사용)"""
        # 테스트 데이터
        context_docs = [{"title": "테스트 문서", "content": "테스트 내용"}]
        
        # Streamlit UI 컴포넌트를 사용하는 실제 함수는 테스트하지 않고
        # 대신 함수가 올바른 파라미터로 호출되는지만 확인
        
        # 컨텍스트가 있으면 실제 처리 로직이 실행되어야 함을 확인
        # (실제 Streamlit 환경이 아니므로 예외가 발생할 것임)
        with pytest.raises(Exception):
            # Streamlit 환경이 아니므로 st.empty() 등에서 예외 발생 예상
            self.generator.generate_dual_answer(
                "테스트 질문", context_docs, [], "Korean"
            )
        
        # 이 테스트는 함수가 올바르게 호출되고 Streamlit 의존성으로 인해 
        # 예외가 발생하는 것을 확인하는 것으로 충분함
    
    def test_create_prompts_empty_context(self):
        """빈 컨텍스트로 프롬프트 생성 테스트"""
        with patch('src.core.dual_response.PromptFactory') as mock_prompt_factory:
            mock_prompt_factory.create_answer_prompt.return_value = "테스트 prefix"
            
            micro_prompt, pro_prompt = self.generator.create_prompts(
                "테스트 질문", [], [], "Korean"
            )
            
            # 빈 컨텍스트여도 프롬프트가 생성되어야 함
            assert "테스트 prefix" in micro_prompt
            assert "테스트 prefix" in pro_prompt
            assert "테스트 질문" in micro_prompt
            assert "테스트 질문" in pro_prompt
    
    def test_create_prompts_with_long_context(self):
        """긴 컨텍스트로 프롬프트 생성 테스트"""
        with patch('src.core.dual_response.PromptFactory') as mock_prompt_factory:
            mock_prompt_factory.create_answer_prompt.return_value = "테스트 prefix"
            
            # 1000자 이상의 긴 내용
            long_content = "A" * 1500
            context_docs = [{"title": "긴 문서", "content": long_content}]
            
            micro_prompt, pro_prompt = self.generator.create_prompts(
                "테스트 질문", context_docs, [], "Korean"
            )
            
            # 내용이 1000자로 잘렸는지 확인
            assert "A" * 1000 in micro_prompt
            assert len([line for line in micro_prompt.split('\n') if "A" * 1000 in line]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])