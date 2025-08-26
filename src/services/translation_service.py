"""
번역 서비스 모듈

Nova Pro를 사용한 게임 용어 번역 서비스를 제공합니다.
기존 translate_text_with_caching() 함수를 클래스 기반으로 리팩토링했습니다.
"""

import json
import re
from typing import Dict, Any, Optional
from src.core.prompt_generator import PromptFactory


class TranslationService:
    """Nova Pro를 사용한 번역 서비스 클래스
    
    게임 용어 단어장을 활용한 고품질 번역을 제공합니다.
    프롬프트 캐싱을 통해 성능과 비용을 최적화합니다.
    """
    
    def __init__(self, aws_client_manager, logger=None):
        """번역 서비스 초기화
        
        Args:
            aws_client_manager: AWS 클라이언트 관리자 인스턴스
            logger: 로깅 인스턴스 (선택사항)
        """
        self.aws_manager = aws_client_manager
        self.logger = logger
        self.bedrock_client = None
        
    def _get_bedrock_client(self):
        """Bedrock 클라이언트 지연 로딩"""
        if not self.bedrock_client:
            self.bedrock_client = self.aws_manager.get_client('bedrock-runtime')
        return self.bedrock_client
    
    def _detect_language(self, text: str) -> str:
        """텍스트 언어 감지
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            str: 감지된 언어 ("Korean" 또는 "English")
        """
        # 한글 포함 여부로 간단한 언어 감지
        if re.search(r'[가-힣]', text):
            return "Korean"
        else:
            return "English"
    
    def _log_token_usage(self, model_id: str, response_body: Dict, operation: str = "번역"):
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
    
    def translate_text_with_caching(self, text: str, target_language: str = "auto") -> Dict[str, Any]:
        """Nova Pro를 사용한 번역 함수 (Nova 전용 프롬프트 캐싱)
        
        Args:
            text: 번역할 텍스트
            target_language: 목표 언어 ("auto", "Korean", "English")
            
        Returns:
            Dict[str, Any]: 번역 결과 딕셔너리
                - original_text: 원본 텍스트
                - detected_language: 감지된 언어
                - target_language: 목표 언어
                - translated_text: 번역된 텍스트
        """
        # 언어 감지 및 타겟 언어 설정
        if target_language == "auto":
            detected_language = self._detect_language(text)
            target_language = "English" if detected_language == "Korean" else "Korean"
        else:
            detected_language = "Korean" if target_language == "English" else "English"
        
        # Prefix (캐싱될 부분) - 단어장 포함
        prefix_prompt = PromptFactory.create_translation_prompt()
        
        # Suffix (변동되는 부분) - 단순화된 프롬프트
        suffix_prompt = f"""
Translate the following text from {detected_language} to {target_language}:

Text to translate: "{text}"

Please provide only the translation result in {target_language}. Use the game terminology glossary above for accurate character and term recognition.

Translation:"""

        try:
            # Nova Pro를 사용한 번역 요청 (Nova 전용 캐싱)
            message = {
                "role": "user",
                "content": [
                    {"text": prefix_prompt, "cachePoint": {"type": "default"}},  # Nova 전용 캐싱
                    {"text": suffix_prompt}
                ]
            }
            
            body = {
                "messages": [message],
                "inferenceConfig": {
                    "max_new_tokens": 500,
                    "temperature": 0.1  # 번역은 낮은 temperature 사용
                }
            }
            
            bedrock_client = self._get_bedrock_client()
            response = bedrock_client.invoke_model(
                body=json.dumps(body),
                modelId='amazon.nova-pro-v1:0',
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            translated_content = response_body['output']['message']['content'][0]['text'].strip()
            
            # 토큰 사용량 로깅
            self._log_token_usage('amazon.nova-pro-v1:0', response_body, f"번역({target_language})")
            
            # 디버깅 정보
            print(f"=== Nova 번역 디버깅 ===")
            print(f"입력: {text}")
            print(f"출력: {translated_content}")
            print(f"타겟 언어: {target_language}")
            print("=" * 25)
            
            # 번역 결과가 비어있거나 원본과 동일한 경우 처리
            if not translated_content or translated_content == text:
                print("번역 결과가 비어있거나 원본과 동일함")
                translated_content = text
            
            return {
                "original_text": text,
                "detected_language": detected_language,
                "target_language": target_language,
                "translated_text": translated_content
            }
                
        except Exception as e:
            error_msg = f"번역 API 호출 오류: {e}"
            print(error_msg)
            if self.logger:
                self.logger.log_error(error_msg)
            
            # 오류 시 원본 텍스트 반환
            return {
                "original_text": text,
                "detected_language": detected_language,
                "target_language": target_language,
                "translated_text": text
            }
    
    def translate_to_korean(self, text: str) -> Dict[str, Any]:
        """영어 텍스트를 한국어로 번역
        
        Args:
            text: 번역할 영어 텍스트
            
        Returns:
            Dict[str, Any]: 번역 결과
        """
        return self.translate_text_with_caching(text, "Korean")
    
    def translate_to_english(self, text: str) -> Dict[str, Any]:
        """한국어 텍스트를 영어로 번역
        
        Args:
            text: 번역할 한국어 텍스트
            
        Returns:
            Dict[str, Any]: 번역 결과
        """
        return self.translate_text_with_caching(text, "English")
    
    def get_translation_only(self, text: str, target_language: str = "auto") -> str:
        """번역된 텍스트만 반환하는 편의 메서드
        
        Args:
            text: 번역할 텍스트
            target_language: 목표 언어
            
        Returns:
            str: 번역된 텍스트
        """
        result = self.translate_text_with_caching(text, target_language)
        return result["translated_text"]