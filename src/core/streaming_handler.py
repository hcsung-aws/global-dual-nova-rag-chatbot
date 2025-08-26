"""
스트리밍 응답 처리 통합 모듈
"""

import json
import time
from typing import Iterator, Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass
class StreamingTask:
    """스트리밍 작업 정의"""
    task_id: str
    model_id: str
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.3
    callback: Optional[Callable[[str], None]] = None


@dataclass
class StreamingResult:
    """스트리밍 결과"""
    task_id: str
    content: str
    is_complete: bool = False
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StreamingHandler:
    """범용 스트리밍 응답 처리 클래스"""
    
    def __init__(self, aws_clients: Dict[str, Any], logger=None):
        """StreamingHandler 초기화"""
        self.aws_clients = aws_clients
        self.logger = logger
        
        # Bedrock 클라이언트 확인
        if 'bedrock' not in aws_clients and 'bedrock-runtime' not in aws_clients:
            raise ValueError("AWS Bedrock 클라이언트가 필요합니다")
        
        self.bedrock_client = aws_clients.get('bedrock') or aws_clients.get('bedrock-runtime')
    
    def _parse_prompt_for_caching(self, prompt: str) -> List[Dict[str, Any]]:
        """프롬프트를 캐싱 가능한 부분과 동적 부분으로 분리 (기존 로직 완전 통합)"""
        lines = prompt.split('\n')
        
        # 캐싱 경계 찾기 (더 정확한 감지 - 기존 로직과 동일)
        cache_boundary = -1
        for i, line in enumerate(lines):
            if any(marker in line for marker in [
                "## Current Task:", "## 현재 작업:", 
                "Based on the following documents", "다음 문서들을 참고하여",
                "I previously provided", "앞서",
                "Question:", "질문:",
                "Requirements:", "요구사항:"
            ]):
                cache_boundary = i
                break
        
        # 캐싱 경계를 찾지 못한 경우, 프롬프트 길이의 60% 지점을 경계로 설정
        if cache_boundary == -1 and len(lines) > 10:
            cache_boundary = int(len(lines) * 0.6)
            print(f"=== 자동 캐싱 경계 설정 ===")
            print(f"경계를 찾지 못해 {cache_boundary}번째 줄로 설정")
            print("=" * 30)
        
        messages = []
        
        if cache_boundary > 3:  # 최소 캐싱 조건 완화 (5 → 3) - 기존과 동일
            # 캐싱 가능한 부분 (단어장 + 시스템 지시사항)
            cached_content = '\n'.join(lines[:cache_boundary])
            
            # 디버깅: 캐싱 정보 출력 (기존 로직과 동일)
            print(f"=== Nova 프롬프트 캐싱 ===")
            print(f"전체 프롬프트 길이: {len(prompt)} 문자")
            print(f"캐싱 부분 길이: {len(cached_content)} 문자")
            print(f"캐싱 비율: {len(cached_content)/len(prompt)*100:.1f}%")
            print(f"캐싱 경계: {cache_boundary}번째 줄")
            print("=" * 30)
            
            # Nova 모델용 캐싱 구조 (cachePoint 사용)
            messages.append({
                "role": "user",
                "content": [
                    {"text": cached_content, "cachePoint": {"type": "default"}}  # Nova 모델용 캐싱
                ]
            })
            
            # 동적 부분
            dynamic_content = '\n'.join(lines[cache_boundary:])
            messages.append({
                "role": "user", 
                "content": [{"text": dynamic_content}]
            })
        else:
            # 캐싱 구조를 찾을 수 없는 경우 전체를 하나의 메시지로 처리
            print(f"=== 캐싱 불가 ===")
            print(f"캐싱 경계를 찾을 수 없음 (경계: {cache_boundary})")
            print("전체 프롬프트를 단일 메시지로 처리")
            print("=" * 20)
            
            messages.append({
                "role": "user",
                "content": [{"text": prompt}]
            })
        
        return messages
    
    def stream_model_response(self, model_id: str, prompt: str, max_tokens: int = 500, 
                            temperature: float = 0.3) -> Iterator[str]:
        """Nova 모델 스트리밍 호출"""
        try:
            # 간단한 메시지 구조
            messages = [{
                "role": "user",
                "content": [{"text": prompt}]
            }]
            
            body = {
                "messages": messages,
                "inferenceConfig": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            # 스트리밍 요청
            response = self.bedrock_client.invoke_model_with_response_stream(
                body=json.dumps(body),
                modelId=model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            # 스트리밍 응답 처리
            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_obj = json.loads(chunk.get('bytes').decode())
                        
                        # contentBlockDelta에서 텍스트 추출
                        if 'contentBlockDelta' in chunk_obj:
                            delta = chunk_obj['contentBlockDelta'].get('delta', {})
                            text_content = delta.get('text', '')
                            if text_content:
                                yield text_content
                                
        except Exception as e:
            error_msg = f"❌ {model_id} 스트리밍 오류: {e}"
            yield error_msg
    
    def stream_model_response_with_caching(self, model_id: str, prompt: str, max_tokens: int = 500, 
                            temperature: float = 0.3) -> Iterator[str]:
        """Nova 모델 스트리밍 호출 (캐싱 지원) - 기존 stream_nova_model 로직 완전 통합"""
        try:
            # 프롬프트를 캐싱 구조로 파싱 (기존 로직과 동일)
            messages = self._parse_prompt_for_caching(prompt)
            
            body = {
                "messages": messages,
                "inferenceConfig": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            # 스트리밍 요청
            response = self.bedrock_client.invoke_model_with_response_stream(
                body=json.dumps(body),
                modelId=model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            # 스트리밍 응답 처리 (기존 로직과 동일)
            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_obj = json.loads(chunk.get('bytes').decode())
                        
                        # contentBlockDelta에서 텍스트 추출
                        if 'contentBlockDelta' in chunk_obj:
                            delta = chunk_obj['contentBlockDelta'].get('delta', {})
                            text_content = delta.get('text', '')
                            if text_content:
                                yield text_content
                        
                        # 메타데이터에서 토큰 사용량 정보 추출 (스트리밍 완료 시) - 기존 로직과 동일
                        if 'messageStop' in chunk_obj:
                            metadata = chunk_obj.get('messageStop', {})
                            if 'stopReason' in metadata:
                                print(f"스트리밍 완료: {metadata.get('stopReason')}")
                                
        except Exception as e:
            error_msg = f"❌ {model_id} 스트리밍 오류: {e}"
            yield error_msg
    
    def apply_typing_effect(self, text_stream: Iterator[str], delay: float = 0.02, 
                          display_callback: Optional[Callable[[str], None]] = None) -> str:
        """타이핑 효과 적용"""
        full_text = ""
        
        try:
            for chunk in text_stream:
                full_text += chunk
                
                if display_callback:
                    display_callback(full_text + "▌")  # 커서 효과
                
                time.sleep(delay)
            
            # 최종 표시 (커서 제거)
            if display_callback:
                display_callback(full_text)
                
        except Exception as e:
            error_msg = f"❌ 타이핑 효과 오류: {e}"
            full_text += error_msg
            
            if display_callback:
                display_callback(full_text)
        
        return full_text
    
    def handle_parallel_streaming(self, tasks: List[StreamingTask], 
                                display_callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, StreamingResult]:
        """병렬 스트리밍 처리"""
        results = {}
        buffers = {task.task_id: [] for task in tasks}
        completion_flags = {task.task_id: False for task in tasks}
        
        def collect_stream(task: StreamingTask):
            """개별 스트리밍 작업 수집"""
            try:
                for chunk in self.stream_model_response_with_caching(
                    task.model_id, task.prompt, task.max_tokens, task.temperature
                ):
                    buffers[task.task_id].append(chunk)
                    
                    # 콜백 호출
                    if task.callback:
                        task.callback(chunk)
                
                completion_flags[task.task_id] = True
                
            except Exception as e:
                error_msg = f"❌ {task.task_id} 오류: {e}"
                buffers[task.task_id].append(error_msg)
                completion_flags[task.task_id] = True
        
        # 병렬 실행
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            # 모든 작업을 백그라운드에서 시작
            futures = [executor.submit(collect_stream, task) for task in tasks]
            
            # 실시간 표시 (첫 번째 작업을 포그라운드로)
            if tasks and display_callback:
                primary_task = tasks[0]
                buffer_index = 0
                
                while not completion_flags[primary_task.task_id] or buffer_index < len(buffers[primary_task.task_id]):
                    # 버퍼에 새로운 내용이 있으면 표시
                    while buffer_index < len(buffers[primary_task.task_id]):
                        chunk = buffers[primary_task.task_id][buffer_index]
                        display_callback(primary_task.task_id, chunk)
                        buffer_index += 1
                    
                    # 완료되지 않았다면 잠시 대기
                    if not completion_flags[primary_task.task_id]:
                        time.sleep(0.02)  # 타이핑 효과
            
            # 모든 작업 완료 대기
            for future in futures:
                future.result()
        
        # 결과 정리
        for task in tasks:
            content = ''.join(buffers[task.task_id])
            results[task.task_id] = StreamingResult(
                task_id=task.task_id,
                content=content,
                is_complete=completion_flags[task.task_id],
                error=None if completion_flags[task.task_id] else "작업 미완료"
            )
        
        return results
    
    def create_dual_streaming_tasks(self, micro_prompt: str, pro_prompt: str, 
                                  model_prefix: str = "amazon.nova") -> List[StreamingTask]:
        """듀얼 모델 스트리밍 작업 생성 (Micro + Pro)"""
        return [
            StreamingTask(
                task_id="micro",
                model_id=f"{model_prefix}-micro-v1:0",
                prompt=micro_prompt,
                max_tokens=1024,
                temperature=0.3
            ),
            StreamingTask(
                task_id="pro",
                model_id=f"{model_prefix}-pro-v1:0",
                prompt=pro_prompt,
                max_tokens=2048,
                temperature=0.5
            )
        ]
    
    def collect_stream_to_buffer(self, model_id: str, prompt: str, buffer: List[str], 
                               completion_flag: List[bool], max_tokens: int = 500, 
                               temperature: float = 0.3):
        """스트리밍 결과를 버퍼에 수집 (기존 버퍼 수집 로직 완전 통합)"""
        try:
            for chunk in self.stream_model_response_with_caching(model_id, prompt, max_tokens, temperature):
                buffer.append(chunk)
            completion_flag[0] = True
        except Exception as e:
            buffer.append(f"❌ {model_id} 오류: {e}")
            completion_flag[0] = True
    
    def stream_with_realtime_display(self, model_id: str, prompt: str, display_callback,
                                   max_tokens: int = 500, temperature: float = 0.3, 
                                   typing_delay: float = 0.02) -> str:
        """실시간 표시와 함께 스트리밍 (기존 실시간 표시 로직 통합)"""
        full_response = ""
        try:
            for chunk in self.stream_model_response_with_caching(model_id, prompt, max_tokens, temperature):
                full_response += chunk
                display_callback(full_response + "▌")  # 커서 효과
                time.sleep(typing_delay)  # 타이핑 효과
            
            # 최종 표시 (커서 제거)
            display_callback(full_response)
            
        except Exception as e:
            error_msg = f"❌ {model_id} 오류: {e}"
            full_response += error_msg
            display_callback(full_response)
        
        return full_response
    
    def log_token_usage(self, model_id: str, response_body: Dict[str, Any], operation: str = "chat"):
        """토큰 사용량 로깅"""
        try:
            usage = response_body.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            total_tokens = usage.get('totalTokens', 0)
            cache_read_tokens = usage.get('cacheReadInputTokenCount', 0)
            cache_write_tokens = usage.get('cacheWriteInputTokenCount', 0)
            
            # 로그 출력
            if self.logger:
                print(f"토큰 사용량 ({operation}) - 모델: {model_id}")
                print(f"입력: {input_tokens:,}, 출력: {output_tokens:,}, 총: {total_tokens:,}")
                print(f"캐시 읽기: {cache_read_tokens:,}, 캐시 쓰기: {cache_write_tokens:,}")
                
                # 캐싱 효과 계산
                if cache_read_tokens > 0 and input_tokens > 0:
                    cache_efficiency = (cache_read_tokens / input_tokens) * 100
                    print(f"캐싱 효율: {cache_efficiency:.1f}%")
                
        except Exception as e:
            if self.logger:
                print(f"토큰 사용량 로깅 오류: {e}")


def create_streaming_handler(aws_clients: Dict[str, Any]) -> StreamingHandler:
    """StreamingHandler 인스턴스 생성 편의 함수"""
    return StreamingHandler(aws_clients)


def stream_with_typing_effect(handler: StreamingHandler, model_id: str, prompt: str,
                            display_callback: Callable[[str], None], **kwargs) -> str:
    """타이핑 효과와 함께 스트리밍 실행 편의 함수"""
    stream = handler.stream_model_response_with_caching(model_id, prompt, **kwargs)
    return handler.apply_typing_effect(stream, display_callback=display_callback)