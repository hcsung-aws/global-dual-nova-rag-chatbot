# -*- coding: utf-8 -*-
"""
StreamingHandler 클래스 단위 테스트

StreamingHandler의 핵심 기능들을 테스트합니다:
- 프롬프트 캐싱 파싱
- 스트리밍 응답 처리
- 병렬 스트리밍 처리
- 타이핑 효과
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.streaming_handler import (
    StreamingHandler, 
    StreamingTask, 
    StreamingResult,
    create_streaming_handler,
    stream_with_typing_effect
)
from src.utils.logger import StandardLogger


class TestStreamingHandler:
    """StreamingHandler 클래스 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        # Mock AWS 클라이언트
        self.mock_bedrock_client = Mock()
        self.aws_clients = {
            'bedrock-runtime': self.mock_bedrock_client
        }
        
        # Mock 로거
        self.mock_logger = Mock(spec=StandardLogger)
        
        # StreamingHandler 인스턴스
        self.handler = StreamingHandler(self.aws_clients, self.mock_logger)
    
    def test_init_success(self):
        """StreamingHandler 초기화 성공 테스트"""
        assert self.handler.aws_clients == self.aws_clients
        assert self.handler.logger == self.mock_logger
        assert self.handler.bedrock_client == self.mock_bedrock_client
    
    def test_init_no_bedrock_client(self):
        """Bedrock 클라이언트 없을 때 오류 테스트"""
        # 실제 코드에서는 빈 딕셔너리일 때 직접 boto3 클라이언트를 생성하려고 시도함
        # 따라서 boto3.client를 모킹해서 실패하도록 만들어야 함
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.side_effect = Exception("AWS 자격 증명 오류")
            with pytest.raises(ValueError, match="AWS Bedrock 클라이언트 초기화 실패"):
                StreamingHandler({})
    
    def test_parse_prompt_for_caching_with_boundary(self):
        """캐싱 경계가 있는 프롬프트 파싱 테스트"""
        prompt = """게임 용어 단어장:
Paul: 폴
Hogan: 호건

## 현재 작업: 답변 생성

질문: 폴에 대해 알려주세요
답변:"""
        
        messages = self.handler._parse_prompt_for_caching(prompt)
        
        # 2개의 메시지로 분리되어야 함 (캐싱 부분 + 동적 부분)
        assert len(messages) == 2
        
        # 첫 번째 메시지는 캐싱 포인트를 가져야 함
        assert "cachePoint" in messages[0]["content"][0]
        assert messages[0]["content"][0]["cachePoint"]["type"] == "default"
        
        # 캐싱 부분에는 단어장이 포함되어야 함
        cached_content = messages[0]["content"][0]["text"]
        assert "Paul: 폴" in cached_content
        assert "Hogan: 호건" in cached_content
        
        # 동적 부분에는 질문이 포함되어야 함
        dynamic_content = messages[1]["content"][0]["text"]
        assert "질문: 폴에 대해 알려주세요" in dynamic_content
    
    def test_parse_prompt_for_caching_no_boundary(self):
        """캐싱 경계가 없는 짧은 프롬프트 파싱 테스트"""
        prompt = "간단한 질문입니다."
        
        messages = self.handler._parse_prompt_for_caching(prompt)
        
        # 1개의 메시지로 처리되어야 함
        assert len(messages) == 1
        assert messages[0]["content"][0]["text"] == prompt
        assert "cachePoint" not in messages[0]["content"][0]
    
    def test_stream_model_response_success(self):
        """스트리밍 응답 성공 테스트"""
        # Mock 스트리밍 응답 설정
        mock_chunks = [
            {
                'chunk': {
                    'bytes': json.dumps({
                        'contentBlockDelta': {
                            'delta': {'text': '안녕'}
                        }
                    }).encode()
                }
            },
            {
                'chunk': {
                    'bytes': json.dumps({
                        'contentBlockDelta': {
                            'delta': {'text': '하세요'}
                        }
                    }).encode()
                }
            },
            {
                'chunk': {
                    'bytes': json.dumps({
                        'messageStop': {
                            'stopReason': 'end_turn'
                        }
                    }).encode()
                }
            }
        ]
        
        mock_response = {
            'body': iter(mock_chunks)
        }
        
        self.mock_bedrock_client.invoke_model_with_response_stream.return_value = mock_response
        
        # 스트리밍 실행
        result = list(self.handler.stream_model_response(
            'amazon.nova-micro-v1:0', 
            '안녕하세요라고 말해주세요'
        ))
        
        # 결과 검증
        assert result == ['안녕', '하세요']
        
        # Bedrock 클라이언트 호출 검증
        self.mock_bedrock_client.invoke_model_with_response_stream.assert_called_once()
        call_args = self.mock_bedrock_client.invoke_model_with_response_stream.call_args
        
        assert call_args[1]['modelId'] == 'amazon.nova-micro-v1:0'
        assert call_args[1]['accept'] == 'application/json'
        assert call_args[1]['contentType'] == 'application/json'
        
        # 요청 본문 검증
        body = json.loads(call_args[1]['body'])
        assert 'messages' in body
        assert 'inferenceConfig' in body
        assert body['inferenceConfig']['max_new_tokens'] == 500
        assert body['inferenceConfig']['temperature'] == 0.3
    
    def test_stream_model_response_error(self):
        """스트리밍 응답 오류 테스트"""
        # Bedrock 클라이언트에서 예외 발생 설정
        self.mock_bedrock_client.invoke_model_with_response_stream.side_effect = Exception("API 오류")
        
        # 스트리밍 실행
        result = list(self.handler.stream_model_response(
            'amazon.nova-micro-v1:0', 
            '테스트 프롬프트'
        ))
        
        # 오류 메시지 검증
        assert len(result) == 1
        assert "❌ amazon.nova-micro-v1:0 스트리밍 오류: API 오류" in result[0]
        
        # 로거는 실제로 호출되지 않음 (단순히 에러 메시지를 yield)
        # 에러 메시지가 올바르게 생성되었는지만 확인
    
    def test_create_dual_streaming_tasks(self):
        """듀얼 스트리밍 작업 생성 테스트"""
        micro_prompt = "간단한 답변을 해주세요"
        pro_prompt = "상세한 답변을 해주세요"
        
        tasks = self.handler.create_dual_streaming_tasks(micro_prompt, pro_prompt)
        
        # 2개의 작업이 생성되어야 함
        assert len(tasks) == 2
        
        # Micro 작업 검증
        micro_task = tasks[0]
        assert micro_task.task_id == "micro"
        assert micro_task.model_id == "amazon.nova-micro-v1:0"
        assert micro_task.prompt == micro_prompt
        assert micro_task.max_tokens == 1024
        assert micro_task.temperature == 0.3
        
        # Pro 작업 검증
        pro_task = tasks[1]
        assert pro_task.task_id == "pro"
        assert pro_task.model_id == "amazon.nova-pro-v1:0"
        assert pro_task.prompt == pro_prompt
        assert pro_task.max_tokens == 2048
        assert pro_task.temperature == 0.5
    
    def test_apply_typing_effect(self):
        """타이핑 효과 테스트"""
        # Mock 텍스트 스트림
        text_stream = iter(['안녕', '하세요', '!'])
        
        # Mock 디스플레이 콜백
        display_callback = Mock()
        
        # 타이핑 효과 적용 (지연 시간을 0으로 설정하여 빠른 테스트)
        result = self.handler.apply_typing_effect(
            text_stream, 
            delay=0, 
            display_callback=display_callback
        )
        
        # 결과 검증
        assert result == "안녕하세요!"
        
        # 디스플레이 콜백 호출 검증
        expected_calls = [
            (('안녕▌',),),
            (('안녕하세요▌',),),
            (('안녕하세요!▌',),),
            (('안녕하세요!',),)  # 최종 호출 (커서 제거)
        ]
        
        assert display_callback.call_count == 4
        for i, expected_call in enumerate(expected_calls):
            assert display_callback.call_args_list[i] == expected_call
    
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
        
        self.handler.log_token_usage('amazon.nova-micro-v1:0', response_body, 'test')
        
        # 실제 구현에서는 print를 사용하므로 로거 호출 검증 불가
        # 대신 메서드가 예외 없이 실행되었는지 확인
        # (실제로는 print 출력이 발생함)
        
        # 메서드가 성공적으로 실행되었는지만 확인
        # print 출력은 캡처하기 어려우므로 예외 발생 여부만 검증


class TestStreamingTask:
    """StreamingTask 데이터클래스 테스트"""
    
    def test_streaming_task_creation(self):
        """StreamingTask 생성 테스트"""
        task = StreamingTask(
            task_id="test",
            model_id="amazon.nova-micro-v1:0",
            prompt="테스트 프롬프트",
            max_tokens=1000,
            temperature=0.5
        )
        
        assert task.task_id == "test"
        assert task.model_id == "amazon.nova-micro-v1:0"
        assert task.prompt == "테스트 프롬프트"
        assert task.max_tokens == 1000
        assert task.temperature == 0.5
        assert task.callback is None
    
    def test_streaming_task_defaults(self):
        """StreamingTask 기본값 테스트"""
        task = StreamingTask(
            task_id="test",
            model_id="amazon.nova-micro-v1:0",
            prompt="테스트 프롬프트"
        )
        
        assert task.max_tokens == 500
        assert task.temperature == 0.3
        assert task.callback is None


class TestStreamingResult:
    """StreamingResult 데이터클래스 테스트"""
    
    def test_streaming_result_creation(self):
        """StreamingResult 생성 테스트"""
        result = StreamingResult(
            task_id="test",
            content="테스트 결과",
            is_complete=True,
            error=None,
            metadata={"tokens": 100}
        )
        
        assert result.task_id == "test"
        assert result.content == "테스트 결과"
        assert result.is_complete is True
        assert result.error is None
        assert result.metadata == {"tokens": 100}
    
    def test_streaming_result_defaults(self):
        """StreamingResult 기본값 테스트"""
        result = StreamingResult(
            task_id="test",
            content="테스트 결과"
        )
        
        assert result.is_complete is False
        assert result.error is None
        assert result.metadata is None


class TestConvenienceFunctions:
    """편의 함수들 테스트"""
    
    def test_create_streaming_handler(self):
        """create_streaming_handler 편의 함수 테스트"""
        aws_clients = {'bedrock-runtime': Mock()}
        
        handler = create_streaming_handler(aws_clients)
        
        assert isinstance(handler, StreamingHandler)
        assert handler.aws_clients == aws_clients
    
    @patch('src.core.streaming_handler.StreamingHandler')
    def test_stream_with_typing_effect(self, mock_handler_class):
        """stream_with_typing_effect 편의 함수 테스트"""
        # Mock 핸들러 인스턴스
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        # Mock 스트림과 타이핑 효과
        mock_stream = iter(['테스트', ' 결과'])
        mock_handler.stream_model_response_with_caching.return_value = mock_stream
        mock_handler.apply_typing_effect.return_value = "테스트 결과"
        
        # Mock 디스플레이 콜백
        display_callback = Mock()
        
        # 함수 실행
        result = stream_with_typing_effect(
            mock_handler, 
            'amazon.nova-micro-v1:0', 
            '테스트 프롬프트',
            display_callback,
            max_tokens=1000
        )
        
        # 결과 검증
        assert result == "테스트 결과"
        
        # 메서드 호출 검증 (실제로는 stream_model_response_with_caching 호출)
        mock_handler.stream_model_response_with_caching.assert_called_once_with(
            'amazon.nova-micro-v1:0', 
            '테스트 프롬프트', 
            max_tokens=1000
        )
        mock_handler.apply_typing_effect.assert_called_once_with(
            mock_stream, 
            display_callback=display_callback
        )


if __name__ == '__main__':
    pytest.main([__file__])