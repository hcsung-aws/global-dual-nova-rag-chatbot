"""
Bedrock 서비스 모듈

Amazon Bedrock Nova 모델을 사용한 AI 서비스를 제공합니다.
기존 stream_nova_model() 함수와 Nova 모델 호출 로직을 클래스 기반으로 리팩토링했습니다.
"""

import json
from typing import Dict, Any, Iterator, Optional
from src.core.streaming_handler import StreamingHandler


class BedrockService:
    """Amazon Bedrock Nova 모델 서비스 클래스
    
    Nova Micro, Nova Pro 모델을 사용한 텍스트 생성과 스트리밍을 제공합니다.
    StreamingHandler와 통합하여 일관된 스트리밍 경험을 제공합니다.
    """
    
    def __init__(self, bedrock_client_or_manager, streaming_handler: StreamingHandler = None, logger=None):
        """Bedrock 서비스 초기화
        
        Args:
            bedrock_client_or_manager: Bedrock 클라이언트 또는 AWS 클라이언트 관리자
            streaming_handler: 스트리밍 핸들러 인스턴스 (선택사항)
            logger: 로깅 인스턴스 (선택사항)
        """
        from src.core.aws_clients import AWSClientManager
        
        # 입력이 AWSClientManager인지 단일 클라이언트인지 판단
        if isinstance(bedrock_client_or_manager, AWSClientManager):
            self.aws_manager = bedrock_client_or_manager
            self.bedrock_client = None
        else:
            # 단일 클라이언트인 경우 (이전 버전 호환성)
            self.aws_manager = None
            self.bedrock_client = bedrock_client_or_manager
        
        self.logger = logger
        
        # StreamingHandler 설정
        if streaming_handler:
            self.streaming_handler = streaming_handler
        else:
            # StreamingHandler에 필요한 클라이언트 딕셔너리 구성
            if self.aws_manager:
                clients = self.aws_manager.initialize_clients(['bedrock-runtime'])
            else:
                clients = {'bedrock-runtime': self.bedrock_client}
            self.streaming_handler = StreamingHandler(clients)
    
    def _get_bedrock_client(self):
        """Bedrock Runtime 클라이언트 지연 로딩"""
        if not self.bedrock_client:
            if self.aws_manager:
                self.bedrock_client = self.aws_manager.get_client('bedrock-runtime')
            else:
                # 이미 클라이언트가 설정된 경우
                pass
        return self.bedrock_client
    
    def _log_token_usage(self, model_id: str, response_body: Dict, operation: str = "모델 호출"):
        """토큰 사용량 로깅
        
        Args:
            model_id: 사용된 모델 ID
            response_body: API 응답 본문
            operation: 작업 유형
        """
        try:
            usage = response_body.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            total_tokens = usage.get('totalTokens', 0)
            cache_read_tokens = usage.get('cacheReadInputTokenCount', 0)
            cache_write_tokens = usage.get('cacheWriteInputTokenCount', 0)
            
            # 로그 출력
            print(f"=== 토큰 사용량 ({operation}) ===")
            print(f"모델: {model_id}")
            print(f"입력 토큰: {input_tokens:,}")
            print(f"출력 토큰: {output_tokens:,}")
            print(f"총 토큰: {total_tokens:,}")
            print(f"캐시 읽기 토큰: {cache_read_tokens:,}")
            print(f"캐시 쓰기 토큰: {cache_write_tokens:,}")
            
            # 캐싱 효과 계산
            if cache_read_tokens > 0:
                cache_efficiency = (cache_read_tokens / input_tokens) * 100 if input_tokens > 0 else 0
                print(f"캐싱 효율: {cache_efficiency:.1f}%")
            
            print("=" * 40)
            
            # 로거가 있으면 구조화된 로그도 기록
            if self.logger:
                self.logger.log_model_usage(model_id, {
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': total_tokens,
                    'cache_read_tokens': cache_read_tokens,
                    'cache_write_tokens': cache_write_tokens,
                    'operation': operation
                })
                
        except Exception as e:
            print(f"토큰 사용량 로깅 오류: {e}")
            if self.logger:
                self.logger.log_error(f"토큰 사용량 로깅 오류: {e}")
    
    def invoke_model_sync(self, model_id: str, prompt: str, max_tokens: int = 500, 
                         temperature: float = 0.3, use_caching: bool = False) -> Dict[str, Any]:
        """Nova 모델 동기 호출
        
        Args:
            model_id: Nova 모델 ID (예: 'amazon.nova-micro-v1:0', 'amazon.nova-pro-v1:0')
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            use_caching: 프롬프트 캐싱 사용 여부
            
        Returns:
            Dict[str, Any]: 모델 응답
                - content: 생성된 텍스트
                - usage: 토큰 사용량 정보
                - model_id: 사용된 모델 ID
        """
        try:
            bedrock_client = self._get_bedrock_client()
            
            # 메시지 구성
            if use_caching and isinstance(prompt, str):
                # 단순 문자열 프롬프트에 캐싱 적용
                message = {
                    "role": "user",
                    "content": [
                        {"text": prompt, "cachePoint": {"type": "default"}}
                    ]
                }
            elif isinstance(prompt, dict):
                # 이미 구조화된 메시지 사용
                message = prompt
            else:
                # 기본 메시지 구성
                message = {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            
            body = {
                "messages": [message],
                "inferenceConfig": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            response = bedrock_client.invoke_model(
                body=json.dumps(body),
                modelId=model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            content = response_body['output']['message']['content'][0]['text'].strip()
            
            # 토큰 사용량 로깅
            self._log_token_usage(model_id, response_body, f"동기 호출({model_id.split('-')[1]})")
            
            return {
                'content': content,
                'usage': response_body.get('usage', {}),
                'model_id': model_id
            }
            
        except Exception as e:
            error_msg = f"Bedrock 모델 호출 오류 ({model_id}): {e}"
            print(error_msg)
            if self.logger:
                self.logger.log_error(error_msg)
            
            return {
                'content': '',
                'usage': {},
                'model_id': model_id,
                'error': str(e)
            }
    
    def stream_nova_model(self, model_id: str, prompt: str, max_tokens: int = 500, 
                         temperature: float = 0.3) -> Iterator[str]:
        """Nova 모델 스트리밍 호출 (StreamingHandler 통합)
        
        기존 중복 로직을 StreamingHandler로 통합하여 유지보수성 향상
        
        Args:
            model_id: Nova 모델 ID
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            
        Returns:
            Iterator[str]: 스트리밍 텍스트 청크
        """
        return self.streaming_handler.stream_model_response_with_caching(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def invoke_nova_micro(self, prompt: str, max_tokens: int = 1024, 
                         temperature: float = 0.3, use_caching: bool = False) -> Dict[str, Any]:
        """Nova Micro 모델 호출 (빠른 응답용)
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            use_caching: 프롬프트 캐싱 사용 여부
            
        Returns:
            Dict[str, Any]: 모델 응답
        """
        return self.invoke_model_sync(
            model_id='amazon.nova-micro-v1:0',
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            use_caching=use_caching
        )
    
    def invoke_nova_pro(self, prompt: str, max_tokens: int = 2048, 
                       temperature: float = 0.5, use_caching: bool = True) -> Dict[str, Any]:
        """Nova Pro 모델 호출 (상세 분석용)
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            use_caching: 프롬프트 캐싱 사용 여부 (기본값: True)
            
        Returns:
            Dict[str, Any]: 모델 응답
        """
        return self.invoke_model_sync(
            model_id='amazon.nova-pro-v1:0',
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            use_caching=use_caching
        )
    
    def stream_nova_micro(self, prompt: str, max_tokens: int = 1024, 
                         temperature: float = 0.3) -> Iterator[str]:
        """Nova Micro 모델 스트리밍 호출
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            
        Returns:
            Iterator[str]: 스트리밍 텍스트 청크
        """
        return self.stream_nova_model(
            model_id='amazon.nova-micro-v1:0',
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def stream_nova_pro(self, prompt: str, max_tokens: int = 2048, 
                       temperature: float = 0.5) -> Iterator[str]:
        """Nova Pro 모델 스트리밍 호출
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            
        Returns:
            Iterator[str]: 스트리밍 텍스트 청크
        """
        return self.stream_nova_model(
            model_id='amazon.nova-pro-v1:0',
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def stream_with_realtime_display(self, model_id: str, prompt: str, 
                                   display_callback=None, max_tokens: int = 1024, 
                                   temperature: float = 0.3, typing_delay: float = 0.02) -> str:
        """실시간 디스플레이와 함께 스트리밍 (StreamingHandler 위임)
        
        Args:
            model_id: Nova 모델 ID
            prompt: 입력 프롬프트
            display_callback: 실시간 디스플레이 콜백 함수
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            typing_delay: 타이핑 효과 지연 시간
            
        Returns:
            str: 완성된 응답 텍스트
        """
        return self.streaming_handler.stream_with_realtime_display(
            model_id=model_id,
            prompt=prompt,
            display_callback=display_callback,
            max_tokens=max_tokens,
            temperature=temperature,
            typing_delay=typing_delay
        )
    
    def collect_stream_to_buffer(self, model_id: str, prompt: str, buffer: list, 
                               completion_flag: list, max_tokens: int = 2048, 
                               temperature: float = 0.5) -> None:
        """스트림을 버퍼에 수집 (병렬 처리용, StreamingHandler 위임)
        
        Args:
            model_id: Nova 모델 ID
            prompt: 입력 프롬프트
            buffer: 결과를 저장할 버퍼 리스트
            completion_flag: 완료 상태를 나타내는 플래그 리스트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
        """
        self.streaming_handler.collect_stream_to_buffer(
            model_id=model_id,
            prompt=prompt,
            buffer=buffer,
            completion_flag=completion_flag,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Bedrock 서비스 연결 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
                - status: 연결 상태 ("healthy" 또는 "error")
                - available_models: 사용 가능한 모델 목록
                - test_response: 테스트 응답 여부
                - error: 오류 메시지 (오류 시)
        """
        try:
            # Nova Micro로 간단한 테스트 호출
            test_response = self.invoke_nova_micro(
                prompt="Hello", 
                max_tokens=10, 
                temperature=0.1
            )
            
            available_models = ['amazon.nova-micro-v1:0', 'amazon.nova-pro-v1:0']
            
            return {
                'status': 'healthy',
                'available_models': available_models,
                'test_response': bool(test_response.get('content')),
                'client_available': self.bedrock_client is not None,
                'streaming_handler_available': self.streaming_handler is not None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'available_models': [],
                'test_response': False,
                'error': str(e),
                'client_available': False,
                'streaming_handler_available': self.streaming_handler is not None
            }
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """모델 정보 반환
        
        Args:
            model_id: Nova 모델 ID
            
        Returns:
            Dict[str, Any]: 모델 정보
        """
        model_info = {
            'amazon.nova-micro-v1:0': {
                'name': 'Nova Micro',
                'description': '빠른 응답을 위한 경량 모델',
                'recommended_max_tokens': 1024,
                'recommended_temperature': 0.3,
                'use_case': '즉각적인 초기 응답, 간단한 질의응답'
            },
            'amazon.nova-pro-v1:0': {
                'name': 'Nova Pro',
                'description': '상세한 분석을 위한 고성능 모델',
                'recommended_max_tokens': 2048,
                'recommended_temperature': 0.5,
                'use_case': '상세한 분석, 복잡한 추론, 번역'
            }
        }
        
        return model_info.get(model_id, {
            'name': 'Unknown Model',
            'description': '알 수 없는 모델',
            'recommended_max_tokens': 1024,
            'recommended_temperature': 0.3,
            'use_case': '일반적인 텍스트 생성'
        })