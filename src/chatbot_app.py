import streamlit as st
import boto3
import json
import os
import re
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from botocore.config import Config

# GlossaryManager import 추가
from src.utils.glossary_manager import get_glossary_manager

# AWSClientManager import 추가
from src.core.aws_clients import get_aws_client_manager

# PromptFactory import 추가
from src.core.prompt_generator import PromptFactory

# StreamingHandler import 추가
from src.core.streaming_handler import StreamingHandler

# DualResponseGenerator import 추가
from src.core.dual_response import DualResponseGenerator

# TranslationService import 추가
from src.services.translation_service import TranslationService

# KnowledgeBaseService import 추가
from src.services.knowledge_base_service import KnowledgeBaseService

# BedrockService import 추가
from src.services.bedrock_service import BedrockService

# 버전 정보
VERSION = "0.1.0"

st.set_page_config(page_title=f'글로벌 CS 챗봇 v{VERSION} 🌍', page_icon='🌍', layout='wide')

st.markdown(f'''
<div style="text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 2rem;">
    <h1>🌍 글로벌 CS 챗봇 <span style="font-size: 0.6em; opacity: 0.8;">v{VERSION}</span></h1>
    <p>다국어 지원 고객 서비스 (Powered by Nova Micro + Nova Pro + Translation)</p>
</div>
''', unsafe_allow_html=True)

# AWSClientManager를 사용한 클라이언트 관리
@st.cache_resource
def get_aws_clients():
    """
    AWSClientManager를 사용한 AWS 클라이언트 초기화
    기존 함수와의 호환성을 유지하면서 AWSClientManager의 이점을 활용
    """
    print("Running get_aws_clients().")
    try:
        manager = get_aws_client_manager()
        clients = manager.initialize_clients(['s3', 'bedrock-runtime', 'secretsmanager'])
        
        # 중요한 클라이언트 검증 - 더 상세한 로깅
        if 'bedrock-runtime' not in clients or clients.get('bedrock-runtime') is None:
            print("❌ Bedrock Runtime 클라이언트 초기화 실패")
            print(f"사용 가능한 클라이언트: {list(clients.keys())}")
            
            # 직접 생성 시도
            try:
                print("🔄 Bedrock Runtime 클라이언트 직접 생성 시도...")
                import boto3
                from botocore.config import Config
                
                config = Config(
                    read_timeout=60,
                    connect_timeout=10,
                    retries={'max_attempts': 3, 'mode': 'adaptive'}
                )
                
                bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name='us-east-1',
                    config=config
                )
                
                # bedrock-runtime 클라이언트 헬스체크 (invoke_model 메서드 존재 여부 확인)
                if not hasattr(bedrock_client, 'invoke_model'):
                    raise AttributeError("bedrock-runtime 클라이언트에 invoke_model 메서드가 없습니다")
                clients['bedrock-runtime'] = bedrock_client
                print("✅ Bedrock Runtime 클라이언트 직접 생성 성공")
                
            except Exception as direct_error:
                print(f"❌ 직접 생성도 실패: {direct_error}")
                st.error(f"❌ Bedrock Runtime 클라이언트 초기화 실패: {direct_error}")
                st.stop()
        
        print(f"✅ AWS 클라이언트 초기화 완료: {list(clients.keys())}")
        return clients
        
    except Exception as e:
        print(f"❌ AWS 클라이언트 초기화 실패: {e}")
        st.error(f"❌ AWS 클라이언트 초기화 실패: {e}")
        st.stop()

# 전역 클라이언트 매니저 인스턴스
aws_manager = get_aws_client_manager()
clients = get_aws_clients()

# StreamingHandler 인스턴스 생성
try:
    streaming_handler = StreamingHandler(clients)
    print("✅ StreamingHandler 초기화 성공")
except Exception as e:
    st.error(f"❌ StreamingHandler 초기화 실패: {e}")
    st.write("**디버깅 정보:**")
    st.write(f"- 사용 가능한 클라이언트: {list(clients.keys())}")
    st.write(f"- bedrock-runtime 클라이언트: {clients.get('bedrock-runtime', 'None')}")
    st.stop()

# TranslationService 인스턴스 생성
translation_service = TranslationService(aws_manager)

# KnowledgeBaseService 인스턴스 생성
knowledge_base_service = KnowledgeBaseService(aws_manager)

# BedrockService 인스턴스 생성 (StreamingHandler와 통합)
bedrock_service = BedrockService(aws_manager, streaming_handler)

# DualResponseGenerator 인스턴스 생성
dual_response_generator = DualResponseGenerator(streaming_handler)

# 게임 용어 단어장 관리 (GlossaryManager 사용)
def get_game_glossary():
    """게임 용어 단어장을 반환합니다. (GlossaryManager를 통한 중앙화된 관리)"""
    
    try:
        # GlossaryManager를 통해 단어장 로드
        glossary_manager = get_glossary_manager()
        glossary = glossary_manager.get_formatted_glossary()
        
        # 디버깅 정보 출력
        print(f"=== GlossaryManager 단어장 로드 ===")
        print(f"단어장 크기: {len(glossary)} 문자")
        print(f"Paul 포함 여부: {'Paul' in glossary}")
        print(f"Hogan 포함 여부: {'Hogan' in glossary}")
        print(f"Manuel 포함 여부: {'Manuel' in glossary}")
        print(f"Agent C 포함 여부: {'Agent C' in glossary}")
        print("=" * 35)
        
        return glossary
        
    except Exception as e:
        print(f"GlossaryManager 로드 중 오류: {e}")
        # 오류 시에도 기본 단어장 제공 (안정성 보장)
        return "# 게임 용어 단어장 로드 오류\n기본 단어장을 사용합니다."

# 번역 관련 함수들
def create_translation_prompt_prefix():
    """번역을 위한 프롬프트 prefix 생성 (캐싱용)
    
    PromptFactory를 사용하여 번역용 프롬프트를 생성합니다.
    기존 하드코딩된 로직을 통합 시스템으로 교체했습니다.
    """
    return PromptFactory.create_translation_prompt()

def log_token_usage(model_id, response_body, operation="chat"):
    """토큰 사용량 로깅 함수"""
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
            
            # Streamlit에 캐싱 효과 표시
            st.sidebar.success(f"🚀 캐시 효율: {cache_efficiency:.1f}% ({cache_read_tokens:,} 토큰 절약)")
        
        print("=" * 40)
        
    except Exception as e:
        print(f"토큰 사용량 로깅 오류: {e}")

def translate_text_with_caching(text, target_language="auto"):
    """Nova Pro를 사용한 번역 함수 (TranslationService로 통합)
    
    기존 함수와의 호환성을 유지하면서 TranslationService를 사용합니다.
    """
    return translation_service.translate_text_with_caching(text, target_language)



def extract_keywords(query):
    """쿼리에서 키워드 추출 (KnowledgeBaseService로 통합)
    
    기존 함수와의 호환성을 유지하면서 KnowledgeBaseService를 사용합니다.
    """
    return knowledge_base_service._extract_keywords(query)

def search_knowledge_base(query, max_results=5):
    """Bedrock Knowledge Base에서 문서 검색 (KnowledgeBaseService로 통합)
    
    기존 함수와의 호환성을 유지하면서 KnowledgeBaseService를 사용합니다.
    """
    return knowledge_base_service.search_knowledge_base(query, max_results)

def create_answer_prompt_prefix(user_language="Korean"):
    """답변 생성을 위한 프롬프트 prefix 생성 (캐싱용)
    
    PromptFactory를 사용하여 답변 생성용 프롬프트를 생성합니다.
    기존 하드코딩된 로직을 통합 시스템으로 교체했습니다.
    
    Args:
        user_language: 사용자 언어 ("Korean" 또는 "English")
        
    Returns:
        str: 답변 생성용 프롬프트
    """
    # 단어장 로드 상태 디버깅 (기존 디버깅 로직 유지)
    glossary = get_game_glossary()  # 디버깅용으로만 사용
    print(f"=== 답변 프롬프트 생성 디버깅 ===")
    print(f"언어: {user_language}")
    print(f"단어장 크기: {len(glossary)} 문자")
    print(f"Paul 포함: {'Paul' in glossary}")
    print(f"Hogan 포함: {'Hogan' in glossary}")
    print(f"Manuel 포함: {'Manuel' in glossary}")
    print(f"Agent C 포함: {'Agent C' in glossary}")
    print("=" * 40)
    
    return PromptFactory.create_answer_prompt(user_language=user_language)

def create_prompts(user_query, context_docs, conversation_history, user_language="Korean"):
    """각 모델에 맞는 프롬프트 생성 (DualResponseGenerator로 통합)
    
    기존 함수와의 호환성을 유지하면서 DualResponseGenerator를 사용합니다.
    """
    return dual_response_generator.create_prompts(user_query, context_docs, conversation_history, user_language)

def stream_nova_model(model_id, prompt, max_tokens=500, temperature=0.3):
    """Nova 모델 스트리밍 호출 (BedrockService로 통합)
    
    기존 함수와의 호환성을 유지하면서 BedrockService를 사용합니다.
    """
    return bedrock_service.stream_nova_model(model_id, prompt, max_tokens, temperature)

def generate_dual_language_response(query, context_docs, conversation_history, 
                                   micro_prompt_ko, pro_prompt_ko, 
                                   micro_prompt_en, pro_prompt_en):
    """영어 사용자를 위한 이중 언어 답변 생성 (DualResponseGenerator로 통합)
    
    기존 함수와의 호환성을 유지하면서 DualResponseGenerator를 사용합니다.
    """
    return dual_response_generator.generate_dual_language_response(
        query, context_docs, conversation_history, 
        micro_prompt_ko, pro_prompt_ko, 
        micro_prompt_en, pro_prompt_en
    )

def generate_dual_answer(query, context_docs, conversation_history, user_language="Korean"):
    """듀얼 모델을 사용한 답변 생성 (DualResponseGenerator로 통합)
    
    기존 함수와의 호환성을 유지하면서 DualResponseGenerator를 사용합니다.
    """
    return dual_response_generator.generate_dual_answer(query, context_docs, conversation_history, user_language)

# 사이드바
with st.sidebar:
    st.header("🌍 글로벌 CS 설정")
    
    # 언어 선택
    user_language = st.selectbox(
        "🌐 언어 선택 / Language",
        ["한국어 (Korean)", "English"],
        index=0
    )
    
    # 언어 코드 추출
    language_code = "Korean" if "Korean" in user_language else "English"
    
    st.divider()
    
    # 번역 기능
    st.subheader("🔄 실시간 번역")
    
    translation_input = st.text_area(
        "번역할 텍스트 입력 / Enter text to translate:",
        placeholder="게임 관련 텍스트를 입력하세요... / Enter gaming-related text...",
        height=100
    )
    
    if st.button("🔄 번역하기 / Translate"):
        if translation_input.strip():
            with st.spinner("번역 중... / Translating..."):
                # 사용자가 선택한 언어에 따라 번역 방향 결정
                if language_code == "English":
                    # 영어 UI 선택 시: 한국어 → 영어로 번역
                    translation_result = translate_text_with_caching(translation_input, "English")
                else:
                    # 한국어 UI 선택 시: 영어 → 한국어로 번역
                    translation_result = translate_text_with_caching(translation_input, "Korean")
                
                st.success("✅ 번역 완료 / Translation Complete")
                
                # 번역 결과 표시
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**원문 ({translation_result['detected_language']}):**")
                    st.info(translation_result['original_text'])
                
                with col2:
                    st.markdown(f"**번역 ({translation_result['target_language']}):**")
                    st.success(translation_result['translated_text'])
        else:
            st.warning("번역할 텍스트를 입력해주세요. / Please enter text to translate.")
    
    st.divider()
    
    # 토큰 사용량 모니터링
    st.header("📊 토큰 사용량")
    
    try:
        # 최근 1시간 토큰 사용량 조회
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        # CloudWatch 클라이언트 초기화 (오류 처리 포함)
        cloudwatch_client = None
        try:
            cloudwatch_client = aws_manager.get_client('cloudwatch', region_name='us-east-1')
        except Exception as init_error:
            st.error(f"CloudWatch 클라이언트 초기화 실패: {str(init_error)}")
            st.caption("CloudWatch 메트릭 조회를 건너뜁니다.")
            cloudwatch_client = None
        
        # CloudWatch 클라이언트가 성공적으로 초기화된 경우에만 메트릭 조회
        if cloudwatch_client is not None:
            # 토큰 사용량 조회 함수
            def get_token_metrics(model_id, metric_name, label):
                try:
                    response = cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/Bedrock',
                        MetricName=metric_name,
                        Dimensions=[{'Name': 'ModelId', 'Value': model_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=['Sum']
                    )
                    
                    if response['Datapoints']:
                        tokens = int(response['Datapoints'][0]['Sum'])
                        st.metric(label, f"{tokens:,}")
                        return tokens
                    else:
                        st.info(f"{label}: 데이터 없음")
                        return 0
                except Exception as e:
                    st.warning(f"{label} 조회 실패: {str(e)[:50]}...")
                    return 0
            
            # Nova Pro 메트릭
            st.subheader("🧠 Nova Pro")
            pro_input = get_token_metrics('amazon.nova-pro-v1:0', 'InputTokenCount', 'Pro 입력 토큰')
            pro_output = get_token_metrics('amazon.nova-pro-v1:0', 'OutputTokenCount', 'Pro 출력 토큰')
            
            # Nova Micro 메트릭
            st.subheader("⚡ Nova Micro")
            micro_input = get_token_metrics('amazon.nova-micro-v1:0', 'InputTokenCount', 'Micro 입력 토큰')
            micro_output = get_token_metrics('amazon.nova-micro-v1:0', 'OutputTokenCount', 'Micro 출력 토큰')
                
            # 캐시 효율성 확인 (Nova Pro)
            st.subheader("🚀 캐시 효율성")
            try:
                cache_read_response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Bedrock',
                    MetricName='CacheReadInputTokenCount',
                    Dimensions=[{'Name': 'ModelId', 'Value': 'amazon.nova-pro-v1:0'}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                if cache_read_response['Datapoints']:
                    cache_read_tokens = int(cache_read_response['Datapoints'][0]['Sum'])
                    if pro_input > 0:
                        cache_efficiency = (cache_read_tokens / pro_input) * 100
                        st.metric("Pro 캐시 효율", f"{cache_efficiency:.1f}%", f"{cache_read_tokens:,} 토큰 절약")
                    else:
                        st.metric("Pro 캐시 읽기", f"{cache_read_tokens:,}")
                else:
                    st.info("Pro 캐시 데이터 없음")
            except Exception as e:
                st.warning(f"Pro 캐시 조회 실패: {str(e)[:50]}...")
                
            # 총 사용량 표시
            total_input = pro_input + micro_input
            total_output = pro_output + micro_output
            if total_input > 0 or total_output > 0:
                st.subheader("📊 총 사용량 (1시간)")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("총 입력 토큰", f"{total_input:,}")
                with col2:
                    st.metric("총 출력 토큰", f"{total_output:,}")
            
    except Exception as e:
        st.error(f"토큰 모니터링 전체 오류: {str(e)[:100]}...")
        st.caption("CloudWatch 메트릭 조회 권한을 확인해주세요.")
        
        # 디버깅 정보 표시
        with st.expander("🔍 디버깅 정보"):
            st.code(f"오류 상세: {str(e)}")
            st.code(f"AWS 리전: us-east-1")
            
            # CloudWatch 클라이언트가 정의된 경우에만 표시
            if 'cloudwatch_client' in locals() and cloudwatch_client is not None:
                st.code(f"CloudWatch 클라이언트: {type(cloudwatch_client)}")
                
                # 사용 가능한 메트릭 확인 시도
                try:
                    metrics = cloudwatch_client.list_metrics(Namespace='AWS/Bedrock')
                    st.code(f"사용 가능한 메트릭 수: {len(metrics.get('Metrics', []))}")
                except Exception as list_error:
                    st.code(f"메트릭 목록 조회 실패: {str(list_error)}")
            else:
                st.code("CloudWatch 클라이언트: 초기화되지 않음")
                st.code(f"메트릭 목록 조회 실패: {str(list_error)}")

    # 시스템 상태
    st.header("📊 시스템 상태")
    
    # Knowledge Base 상태 확인
    try:
        bedrock_agent_client = aws_manager.get_client('bedrock-agent-runtime', region_name='us-east-1')
        # 간단한 테스트 쿼리로 Knowledge Base 상태 확인
        test_response = bedrock_agent_client.retrieve(
            knowledgeBaseId='SJJP9YYPHX',
            retrievalQuery={'text': 'test'},
            retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 1}}
        )
        st.success("✅ Knowledge Base 연결됨")
        st.caption(f"Knowledge Base ID: SJJP9YYPHX")
        
        # 검색 결과 수 표시
        result_count = len(test_response.get('retrievalResults', []))
        if result_count > 0:
            st.info(f"📚 Knowledge Base 응답 가능")
        else:
            st.warning("⚠️ Knowledge Base에 문서가 없거나 검색 결과 없음")
            
    except Exception as e:
        st.error("❌ Knowledge Base 연결 실패")
        st.caption(f"오류: {str(e)[:100]}...")
    
    st.divider()
    st.subheader("🤖 AI 모델 정보")
    st.info("**Nova Micro + Nova Pro + Translation**")
    st.caption("• ⚡ Nova Micro: 즉각적인 초기 응답")
    st.caption("• 🧠 Nova Pro: 상세한 최종 답변")
    st.caption("• 🌍 Nova Pro: 고품질 게임 용어 번역")
    st.caption("• 🔄 병렬 처리로 빠른 응답")
    st.caption("• 📡 실시간 스트리밍")
    st.caption("• 💰 프롬프트 캐싱으로 비용 절약")
    
    st.divider()
    st.subheader("💡 사용 팁")
    if language_code == "English":
        st.markdown("""
        - **Keyword Search**: "Amazon Survival", "CS Response" etc.
        - **Specific Questions**: "How to fix game execution error?"
        - **Complex Questions**: "Amazon Survival characters and worldview"
        - **Development Related**: "Local server setup", "Dev environment"
        - References previous conversations
        - **New Features**: Quick initial response + Detailed final answer
        - **Translation**: Real-time gaming terminology translation
        """)
    else:
        st.markdown("""
        - **키워드 검색**: "아마존 생존기", "CS 답변" 등
        - **구체적 질문**: "게임 실행 오류 해결 방법은?"
        - **복합 질문**: "아마존 생존기 등장인물과 세계관"
        - **개발 관련**: "로컬서버 설정", "개발 환경"
        - 이전 대화를 참고합니다
        - **새로운 기능**: 빠른 초기 응답 + 상세한 최종 답변
        - **번역 기능**: 실시간 게임 용어 번역
        """)
    
    if st.button("🗑️ 대화 기록 삭제 / Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# 메인 채팅 인터페이스
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    with st.chat_message("assistant"):
        if language_code == "English":
            st.markdown("""
            Hello! I'm the Global CS Chatbot. 🌍
            
            **Upgraded with Nova Micro + Nova Pro + Translation** for faster and more accurate responses!
            
            ⚡ **Nova Micro**: Instant initial response within 1 second  
            🧠 **Nova Pro**: Detailed final response generated in background  
            🌍 **Translation**: Real-time gaming terminology translation  
            🔄 **Parallel Processing**: Both models work simultaneously to minimize latency
            
            I can answer questions based on **36 documents** and provide real-time translation for gaming terminology.
            Feel free to ask me anything!
            
            **Example Questions:**
            - "Tell me about Amazon Survival in detail"
            - "What are the CS response formats and guidelines?"
            - "How to solve game execution problems?"
            - "Please explain local server setup step by step"
            - "What are the characteristics of Amazon Survival characters?"
            """)
        else:
            st.markdown("""
            안녕하세요! 글로벌 CS 챗봇입니다. 🌍
            
            **Nova Micro + Nova Pro + Translation**으로 업그레이드되어 더욱 빠르고 정확한 답변을 제공합니다!
            
            ⚡ **Nova Micro**: 1초 이내 즉각적인 초기 응답  
            🧠 **Nova Pro**: 백그라운드에서 상세한 최종 답변 생성  
            🌍 **번역 기능**: 실시간 게임 용어 번역  
            🔄 **병렬 처리**: 두 모델이 동시에 작업하여 지연 시간 최소화
            
            **36개의 문서**를 기반으로 질문에 답변하고, 게임 용어 실시간 번역을 제공합니다.
            궁금한 것이 있으시면 언제든 물어보세요!
            
            **예시 질문:**
            - "아마존 생존기에 대해 자세히 알려주세요"
            - "CS 답변 형식과 가이드라인은 무엇인가요?"
            - "게임 실행 관련 문제 해결 방법은?"
            - "로컬서버 설정 방법을 단계별로 알려주세요"
            - "아마존 생존기 등장인물들의 특징은?"
            """)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "references" in message:
            with st.expander("📚 참고 문서 / Reference Documents"):
                for doc in message["references"]:
                    st.markdown(f"**{doc['title']}** (점수: {doc.get('score', 0)})")
                    if 'matched_keywords' in doc and doc['matched_keywords']:
                        st.caption(f"🔍 매칭된 키워드: {', '.join(doc['matched_keywords'])}")
                    st.markdown(doc['content'][:600] + ("..." if len(doc['content']) > 600 else ""))
                    if doc['url'] != '#':
                        st.markdown(f"[원본 보기]({doc['url']})")
                    st.divider()

# 채팅 입력
if language_code == "English":
    prompt_placeholder = "Enter your question..."
else:
    prompt_placeholder = "질문을 입력하세요..."

if prompt := st.chat_input(prompt_placeholder):
    # 번역 기능 추가 - 사용자 입력이 다른 언어인 경우 번역
    original_prompt = prompt
    detected_language = "Korean" if re.search(r'[가-힣]', prompt) else "English"
    
    # 사용자가 선택한 언어와 입력 언어가 다른 경우 번역
    if (language_code == "Korean" and detected_language == "English") or \
       (language_code == "English" and detected_language == "Korean"):
        
        with st.spinner("Nova Pro가 질문을 번역 중... / Nova Pro is translating question..."):
            translation_result = translate_text_with_caching(prompt, language_code)
            translated_prompt = translation_result['translated_text']
            
            # 번역된 질문 표시
            st.info(f"🔄 번역된 질문 / Translated Question: {translated_prompt}")
            prompt = translated_prompt
    
    st.session_state.messages.append({"role": "user", "content": original_prompt})
    with st.chat_message("user"):
        st.markdown(original_prompt)

    with st.chat_message("assistant"):
        # Knowledge Base에서 문서 검색
        context_docs = search_knowledge_base(prompt)
        
        # 검색 결과 디버깅 정보 표시
        if context_docs:
            if language_code == "English":
                st.caption(f"🔍 Found {len(context_docs)} documents from Knowledge Base")
            else:
                st.caption(f"🔍 Knowledge Base에서 {len(context_docs)}개 문서 검색됨")
        else:
            if language_code == "English":
                st.caption("🔍 No documents found in Knowledge Base")
            else:
                st.caption("🔍 Knowledge Base에서 검색된 문서 없음")
            
        # 듀얼 모델로 답변 생성
        answer = generate_dual_answer(prompt, context_docs, st.session_state.messages, language_code)
        
        if context_docs:
            with st.expander("📚 참고 문서 / Reference Documents"):
                for doc in context_docs:
                    st.markdown(f"**{doc['title']}** (점수: {doc.get('score', 0):.3f})")
                    st.markdown(doc['content'][:600] + ("..." if len(doc['content']) > 600 else ""))
                    if doc['url'] != '#':
                        st.markdown(f"[원본 보기]({doc['url']})")
                    st.divider()
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer,
                "references": context_docs
            })
        else:
            st.session_state.messages.append({"role": "assistant", "content": answer})

st.divider()
if language_code == "English":
    st.caption("🔄 Knowledge Base provides real-time intelligent search.")
    st.caption("⚡ Provides fast and accurate responses with Nova Micro + Nova Pro dual model.")
    st.caption("🌍 Real-time gaming terminology translation available.")
    st.caption("📚 Powered by Amazon Bedrock Knowledge Base.")
else:
    st.caption("🔄 Knowledge Base가 실시간 지능형 검색을 제공합니다.")
    st.caption("⚡ Nova Micro + Nova Pro 듀얼 모델로 빠르고 정확한 답변을 제공합니다.")
    st.caption("🌍 실시간 게임 용어 번역을 지원합니다.")
    st.caption("📚 Amazon Bedrock Knowledge Base로 구동됩니다.")
