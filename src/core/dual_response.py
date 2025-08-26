"""
이중 언어 응답 생성 모듈

메인 애플리케이션에서 분리된 비즈니스 로직을 담당합니다.
- generate_dual_answer: 듀얼 모델을 사용한 답변 생성
- generate_dual_language_response: 영어 사용자를 위한 이중 언어 답변 생성
- create_prompts: 각 모델에 맞는 프롬프트 생성
"""

import streamlit as st
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Tuple

from src.core.prompt_generator import PromptFactory
from src.core.streaming_handler import StreamingHandler


class DualResponseGenerator:
    """이중 언어 응답 생성기
    
    메인 애플리케이션에서 분리된 비즈니스 로직을 처리합니다.
    UI 로직과 비즈니스 로직을 분리하여 테스트 가능성과 재사용성을 향상시킵니다.
    """
    
    def __init__(self, streaming_handler: StreamingHandler):
        """
        Args:
            streaming_handler: 스트리밍 처리를 담당하는 핸들러
        """
        self.streaming_handler = streaming_handler
    
    def create_prompts(self, user_query: str, context_docs: List[Dict], 
                      conversation_history: List[Dict], user_language: str = "Korean") -> Tuple[str, str]:
        """각 모델에 맞는 프롬프트 생성 (다국어 지원, 캐싱 최적화)
        
        Args:
            user_query: 사용자 질문
            context_docs: 검색된 문서 목록
            conversation_history: 대화 히스토리
            user_language: 사용자 언어 ("Korean" 또는 "English")
            
        Returns:
            Tuple[str, str]: (micro_prompt, pro_prompt)
        """
        # 캐싱 가능한 prefix 생성
        cached_prefix = PromptFactory.create_answer_prompt(user_language=user_language)
        
        # 컨텍스트 준비
        context = ""
        if context_docs:
            context = "\n\n".join([f"제목: {doc['title']}\n내용: {doc['content'][:1000]}" for doc in context_docs])
        
        # 대화 히스토리 준비
        history_context = ""
        if conversation_history:
            recent_history = conversation_history[-4:]
            history_parts = []
            for i in range(0, len(recent_history), 2):
                if i + 1 < len(recent_history):
                    history_parts.append(f"이전 질문: {recent_history[i]['content']}\n이전 답변: {recent_history[i + 1]['content']}")
            if history_parts:
                history_context = f"이전 대화:\n{chr(10).join(history_parts)}\n\n"
        
        # 언어별 프롬프트 조정 (캐싱된 prefix 활용)
        if user_language == "English":
            # 영어 사용자를 위한 프롬프트
            micro_prompt = f"""{cached_prefix}

## Current Task: Provide Concise Overview

{history_context}Based on the following documents, please provide a concise overview:

{context}

Question: {user_query}

Requirements:
- Provide key information in 1-2 paragraphs clearly and concisely
- End with complete sentences
- Finish with a simple connecting phrase like "Let me provide more details."
- Respond in English in a friendly manner
- Keep it brief to avoid incomplete responses
- Use the game terminology glossary above for accurate character and term recognition

Answer:"""

            pro_prompt = f"""{cached_prefix}

## Current Task: Provide Detailed Analysis

{history_context}I previously provided a basic overview for "{user_query}". 
Now, please provide more detailed and professional analysis based on the following documents:

{context}

Question: {user_query}

Requirements:
- Start naturally as an extension of the previous answer (e.g., "Looking more specifically...", "To analyze this in more detail...")
- Include specific examples, pros/cons, use cases, and comparative analysis
- Use markdown for structured and organized answers
- Provide practical and professional insights
- Respond in English in a friendly and professional manner
- Base your answer accurately and in detail on the provided documents
- Explain step-by-step when necessary
- Consider previous conversation context
- Use the game terminology glossary above for accurate character and term recognition

Answer:"""
        else:
            # 한국어 사용자를 위한 프롬프트 (기존)
            micro_prompt = f"""{cached_prefix}

## 현재 작업: 간결한 개요 제공

{history_context}다음 문서들을 참고하여 질문에 대한 간결한 개요를 제공해주세요:

{context}

질문: {user_query}

요구사항:
- 핵심 내용을 1-2개 문단으로 간단명료하게 설명
- 반드시 완전한 문장으로 마무리할 것
- 마지막에 "더 구체적으로 살펴보겠습니다." 같은 간단한 연결 문구로 마무리
- 한국어로 친절하게 답변하세요
- 간결하게 작성하여 답변이 중간에 끊어지지 않도록 해주세요
- 위의 게임 용어 단어장을 활용하여 정확한 캐릭터 및 용어 인식

답변:"""

            pro_prompt = f"""{cached_prefix}

## 현재 작업: 상세한 분석 제공

{history_context}앞서 "{user_query}"에 대한 기본적인 개요를 제공했습니다. 
이제 다음 문서들을 참고하여 그 내용에 자연스럽게 이어서 더 상세하고 전문적인 분석을 제공해주세요:

{context}

질문: {user_query}

요구사항:
- 앞선 답변의 자연스러운 연장선상에서 시작 (예: "더 구체적으로 살펴보면...", "이를 더 자세히 분석하면..." 등)
- 구체적인 예시, 장단점, 사용 사례, 비교 분석을 포함한 심화 내용
- 마크다운을 활용한 체계적이고 구조화된 답변
- 실무적이고 전문적인 관점에서의 깊이 있는 설명
- 한국어로 친절하고 전문적으로 답변하세요
- 제공된 문서 내용을 기반으로 정확하고 상세하게 답변하세요
- 필요시 단계별로 설명해주세요
- 이전 대화 맥락을 고려하여 답변하세요
- 위의 게임 용어 단어장을 활용하여 정확한 캐릭터 및 용어 인식

답변:"""

        return micro_prompt, pro_prompt
    
    def generate_dual_language_response(self, query: str, context_docs: List[Dict], 
                                      conversation_history: List[Dict],
                                      micro_prompt_ko: str, pro_prompt_ko: str, 
                                      micro_prompt_en: str, pro_prompt_en: str) -> str:
        """영어 사용자를 위한 이중 언어 답변 생성 - GitHub 원본 방식 완전 적용
        
        Args:
            query: 사용자 질문
            context_docs: 검색된 문서 목록
            conversation_history: 대화 히스토리
            micro_prompt_ko: 한국어 Micro 프롬프트
            pro_prompt_ko: 한국어 Pro 프롬프트
            micro_prompt_en: 영어 Micro 프롬프트
            pro_prompt_en: 영어 Pro 프롬프트
            
        Returns:
            str: 생성된 이중 언어 응답
        """
        # 응답을 저장할 컨테이너
        response_container = st.empty()
        
        # 1단계: 한국어 답변 생성 (GitHub 원본과 동일한 병렬 실행)
        st.caption("🇰🇷 한국어 답변 생성 중 (담당자 확인용) - GitHub 원본 방식 병렬 처리...")
        
        # Pro 모델의 스트리밍 결과를 저장할 버퍼 (GitHub 원본과 동일)
        korean_pro_buffer = []
        korean_pro_complete = False
        
        def collect_korean_pro_stream():
            """한국어 Pro 모델의 스트리밍 결과를 버퍼에 수집 (StreamingHandler 사용)"""
            nonlocal korean_pro_buffer, korean_pro_complete
            completion_flag = [False]
            # StreamingHandler를 사용하여 버퍼 수집
            self.streaming_handler.collect_stream_to_buffer(
                'amazon.nova-pro-v1:0', pro_prompt_ko, korean_pro_buffer, completion_flag,
                max_tokens=2048, temperature=0.5
            )
            korean_pro_complete = completion_flag[0]
        
        # GitHub 원본과 동일한 ThreadPoolExecutor 병렬 실행
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Pro 모델을 백그라운드에서 시작 (GitHub 원본과 동일)
            future_korean_pro = executor.submit(collect_korean_pro_stream)
            
            # 1단계: Nova Micro 스트리밍 (StreamingHandler 사용)
            korean_micro_response = self.streaming_handler.stream_with_realtime_display(
                model_id='amazon.nova-micro-v1:0',
                prompt=micro_prompt_ko,
                display_callback=lambda text: response_container.markdown(f"## 📋 한국어 답변 (담당자 확인용)\n{text}"),
                max_tokens=1024,
                temperature=0.3,
                typing_delay=0.02
            )
            
            # 2단계: Pro 모델 결과 출력 (GitHub 원본과 동일한 버퍼 처리)
            st.caption("🔍 한국어 상세 분석을 자연스럽게 연결 중...")
            
            buffer_index = 0
            korean_current_display = f"## 📋 한국어 답변 (담당자 확인용)\n{korean_micro_response}\n\n---\n\n**🔍 Nova Pro 상세 분석:**\n\n"
            
            # GitHub 원본과 동일한 버퍼 실시간 출력 방식
            while not korean_pro_complete or buffer_index < len(korean_pro_buffer):
                # 버퍼에 새로운 내용이 있으면 출력
                while buffer_index < len(korean_pro_buffer):
                    chunk = korean_pro_buffer[buffer_index]
                    korean_current_display += chunk
                    response_container.markdown(korean_current_display + "▌")
                    time.sleep(0.01)  # GitHub 원본과 동일한 빠른 타이핑 효과
                    buffer_index += 1
                
                # Pro 모델이 아직 완료되지 않았다면 잠시 대기 (GitHub 원본과 동일)
                if not korean_pro_complete:
                    time.sleep(0.05)
            
            # 한국어 최종 표시 (커서 제거)
            response_container.markdown(korean_current_display)
            
            # Pro 작업 완료 대기 (GitHub 원본과 동일)
            future_korean_pro.result()
            korean_final = korean_current_display
        
        # 2단계: 영어 답변 생성 (GitHub 원본과 동일한 병렬 실행)
        st.caption("🇺🇸 영어 답변 생성 중 (고객용) - GitHub 원본 방식 병렬 처리...")
        
        # Pro 모델의 스트리밍 결과를 저장할 버퍼 (GitHub 원본과 동일)
        english_pro_buffer = []
        english_pro_complete = False
        
        def collect_english_pro_stream():
            """영어 Pro 모델의 스트리밍 결과를 버퍼에 수집 (StreamingHandler 사용)"""
            nonlocal english_pro_buffer, english_pro_complete
            completion_flag = [False]
            # StreamingHandler를 사용하여 버퍼 수집
            self.streaming_handler.collect_stream_to_buffer(
                'amazon.nova-pro-v1:0', pro_prompt_en, english_pro_buffer, completion_flag,
                max_tokens=2048, temperature=0.5
            )
            english_pro_complete = completion_flag[0]
        
        # GitHub 원본과 동일한 ThreadPoolExecutor 병렬 실행
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Pro 모델을 백그라운드에서 시작 (GitHub 원본과 동일)
            future_english_pro = executor.submit(collect_english_pro_stream)
            
            # 1단계: Nova Micro 스트리밍 (StreamingHandler 사용)
            english_micro_response = self.streaming_handler.stream_with_realtime_display(
                model_id='amazon.nova-micro-v1:0',
                prompt=micro_prompt_en,
                display_callback=lambda text: response_container.markdown(f"""{korean_final}

---

## 🌍 English Response (For Customer)
{text}"""),
                max_tokens=1024,
                temperature=0.3,
                typing_delay=0.02
            )
            
            # 2단계: Pro 모델 결과 출력 (GitHub 원본과 동일한 버퍼 처리)
            st.caption("🔍 영어 상세 분석을 자연스럽게 연결 중...")
            
            buffer_index = 0
            english_current_display = f"""{korean_final}

---

## 🌍 English Response (For Customer)
{english_micro_response}

---

**🔍 Nova Pro Detailed Analysis:**

"""
            
            # GitHub 원본과 동일한 버퍼 실시간 출력 방식
            while not english_pro_complete or buffer_index < len(english_pro_buffer):
                # 버퍼에 새로운 내용이 있으면 출력
                while buffer_index < len(english_pro_buffer):
                    chunk = english_pro_buffer[buffer_index]
                    english_current_display += chunk
                    response_container.markdown(english_current_display + "▌")
                    time.sleep(0.01)  # GitHub 원본과 동일한 빠른 타이핑 효과
                    buffer_index += 1
                
                # Pro 모델이 아직 완료되지 않았다면 잠시 대기 (GitHub 원본과 동일)
                if not english_pro_complete:
                    time.sleep(0.05)
            
            # 최종 표시 (커서 제거)
            response_container.markdown(english_current_display)
            
            # Pro 작업 완료 대기 (GitHub 원본과 동일)
            future_english_pro.result()
            
            return english_current_display
    
    def generate_dual_answer(self, query: str, context_docs: List[Dict], 
                           conversation_history: List[Dict], user_language: str = "Korean") -> str:
        """듀얼 모델을 사용한 답변 생성 (완전한 다국어 지원)
        
        Args:
            query: 사용자 질문
            context_docs: 검색된 문서 목록
            conversation_history: 대화 히스토리
            user_language: 사용자 언어 ("Korean" 또는 "English")
            
        Returns:
            str: 생성된 답변
        """
        if not context_docs:
            if user_language == "English":
                return "Sorry, I couldn't find relevant documents. Please try searching with different keywords or rephrase your question."
            else:
                return "죄송합니다. 관련된 문서를 찾을 수 없습니다. 다른 키워드로 검색해보시거나 질문을 다시 작성해주세요."
        
        # 사용자 언어에 따라 프롬프트 생성
        if user_language == "English":
            # 영어 사용자: 한국어 답변 + 영어 답변 모두 생성
            # 1단계: 한국어로 답변 생성 (담당자 확인용)
            micro_prompt_ko, pro_prompt_ko = self.create_prompts(query, context_docs, conversation_history, "Korean")
            
            # 2단계: 영어로 답변 생성 (고객용)
            micro_prompt_en, pro_prompt_en = self.create_prompts(query, context_docs, conversation_history, "English")
            
            return self.generate_dual_language_response(query, context_docs, conversation_history, 
                                                      micro_prompt_ko, pro_prompt_ko, 
                                                      micro_prompt_en, pro_prompt_en)
        else:
            # 한국어 사용자: GitHub 원본과 100% 동일한 병렬 실행
            micro_prompt, pro_prompt = self.create_prompts(query, context_docs, conversation_history, "Korean")
            
            # 응답을 저장할 컨테이너
            response_container = st.empty()
            
            # StreamingHandler를 사용한 병렬 스트리밍 (기존 로직 통합)
            pro_buffer = []
            pro_complete = False
            
            def collect_pro_stream():
                """Pro 모델의 스트리밍 결과를 버퍼에 수집 (StreamingHandler 사용)"""
                nonlocal pro_buffer, pro_complete
                completion_flag = [False]
                # StreamingHandler를 사용하여 버퍼 수집
                self.streaming_handler.collect_stream_to_buffer(
                    'amazon.nova-pro-v1:0', pro_prompt, pro_buffer, completion_flag,
                    max_tokens=2048, temperature=0.5
                )
                pro_complete = completion_flag[0]
            
            # GitHub 원본과 동일한 ThreadPoolExecutor 병렬 실행
            with ThreadPoolExecutor(max_workers=2) as executor:
                st.caption("🚀 StreamingHandler 통합: Nova Micro + Pro 병렬 실행...")
                
                # Pro 모델을 백그라운드에서 시작 (GitHub 원본과 동일)
                future_pro = executor.submit(collect_pro_stream)
                
                # 1단계: Nova Micro 스트리밍 (StreamingHandler 사용)
                full_micro_response = self.streaming_handler.stream_with_realtime_display(
                    model_id='amazon.nova-micro-v1:0',
                    prompt=micro_prompt,
                    display_callback=lambda text: response_container.markdown(text),
                    max_tokens=1024,
                    temperature=0.3,
                    typing_delay=0.02
                )
                
                # 2단계: Pro 모델 결과 출력 (GitHub 원본과 동일한 버퍼 처리)
                st.caption("🔍 Nova Pro 상세 답변을 자연스럽게 연결 중...")
                
                buffer_index = 0
                current_display = full_micro_response + "\n\n---\n\n**🔍 Nova Pro 상세 분석:**\n\n"
                
                # GitHub 원본과 동일한 버퍼 실시간 출력 방식
                while not pro_complete or buffer_index < len(pro_buffer):
                    # 버퍼에 새로운 내용이 있으면 출력
                    while buffer_index < len(pro_buffer):
                        chunk = pro_buffer[buffer_index]
                        current_display += chunk
                        response_container.markdown(current_display + "▌")
                        time.sleep(0.01)  # GitHub 원본과 동일한 빠른 타이핑 효과
                        buffer_index += 1
                    
                    # Pro 모델이 아직 완료되지 않았다면 잠시 대기 (GitHub 원본과 동일)
                    if not pro_complete:
                        time.sleep(0.05)
                
                # 최종 표시 (커서 제거)
                response_container.markdown(current_display)
                
                # Pro 작업 완료 대기 (GitHub 원본과 동일)
                future_pro.result()
                
                return current_display