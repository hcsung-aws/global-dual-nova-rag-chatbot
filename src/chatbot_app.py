import streamlit as st
import boto3
import json
import os
import re
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from botocore.config import Config

st.set_page_config(page_title='글로벌 CS 챗봇 🌍', page_icon='🌍', layout='wide')

st.markdown('''
<div style="text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 2rem;">
    <h1>🌍 글로벌 CS 챗봇</h1>
    <p>다국어 지원 고객 서비스 (Powered by Nova Micro + Nova Pro + Translation)</p>
</div>
''', unsafe_allow_html=True)

@st.cache_resource
def get_aws_clients():
    config = Config(
        read_timeout=60,
        connect_timeout=10,
        retries={'max_attempts': 3}
    )
    return {
        's3': boto3.client('s3'),
        'bedrock': boto3.client('bedrock-runtime', config=config),
        'secrets': boto3.client('secretsmanager')
    }

clients = get_aws_clients()

# 게임 용어 단어장 (하드코딩으로 S3 로드 실패 방지)
def get_game_glossary():
    """게임 용어 단어장을 반환합니다. (S3 로드 실패 방지를 위해 하드코딩)"""
    
    # 완전한 게임 용어 단어장을 프롬프트에 직접 포함
    glossary = """# 게임 용어 단어장 (한국어 <-> 영어)
# 형식: 한국어 용어 | 영어 용어 | 설명

# 캐릭터 이름
주인공 | Paul | 주인공 캐릭터 이름
공대한 | Hogan | 게임 내 캐릭터 공대한 이름
마누엘 | Manuel | 게임 내 조연 캐릭터 이름
에이전트 C | Agent C | 게임 내 조연 캐릭터 이름

# 기본 게임 용어
레벨업 | Level Up | 캐릭터의 레벨이 상승하는 것
경험치 | Experience Points (XP) | 캐릭터 성장을 위한 포인트
체력 | Health Points (HP) | 캐릭터의 생명력
마나 | Mana Points (MP) | 마법 사용을 위한 포인트
스킬 | Skill | 캐릭터가 사용할 수 있는 특수 능력
아이템 | Item | 게임 내에서 획득할 수 있는 물건
인벤토리 | Inventory | 아이템을 보관하는 공간
퀘스트 | Quest | 게임 내 임무나 과제
던전 | Dungeon | 몬스터가 있는 지하 공간
보스 | Boss | 강력한 적 몬스터
길드 | Guild | 플레이어들의 조합이나 클랜
파티 | Party | 함께 게임을 하는 플레이어 그룹
PvP | Player vs Player | 플레이어 대 플레이어 전투
PvE | Player vs Environment | 플레이어 대 환경(몬스터) 전투
NPC | Non-Player Character | 컴퓨터가 조작하는 캐릭터

# 전투 관련 용어
공격력 | Attack Power | 공격 시 가하는 데미지
방어력 | Defense | 받는 데미지를 줄이는 능력
크리티컬 | Critical Hit | 치명타, 높은 데미지를 주는 공격
버프 | Buff | 능력치를 향상시키는 효과
디버프 | Debuff | 능력치를 감소시키는 효과
힐링 | Healing | 체력을 회복하는 것
리스폰 | Respawn | 죽은 후 다시 살아나는 것
쿨다운 | Cooldown | 스킬 재사용 대기시간
콤보 | Combo | 연속 공격
도트 데미지 | Damage over Time (DoT) | 지속 데미지

# 아이템 관련 용어
장비 | Equipment | 캐릭터가 착용하는 아이템
무기 | Weapon | 공격용 장비
방어구 | Armor | 방어용 장비
소모품 | Consumable | 사용하면 없어지는 아이템
레어 아이템 | Rare Item | 희귀한 아이템
에픽 아이템 | Epic Item | 매우 희귀한 아이템
레전더리 | Legendary | 전설급 아이템
세트 아이템 | Set Item | 세트로 착용하면 추가 효과가 있는 아이템
강화 | Enhancement/Upgrade | 아이템의 성능을 향상시키는 것
인챈트 | Enchant | 아이템에 마법 효과를 부여하는 것

# 게임 시스템 용어
서버 | Server | 게임이 운영되는 컴퓨터
채널 | Channel | 서버 내의 구역
로그인 | Login | 게임에 접속하는 것
로그아웃 | Logout | 게임에서 나가는 것
세이브 | Save | 게임 진행 상황을 저장하는 것
로드 | Load | 저장된 게임을 불러오는 것
패치 | Patch | 게임 업데이트
버그 | Bug | 게임의 오류나 결함
래그 | Lag | 네트워크 지연으로 인한 끊김 현상
핑 | Ping | 네트워크 응답 속도

# 캐릭터 관련 용어
캐릭터 | Character | 플레이어가 조작하는 게임 내 인물
클래스 | Class | 캐릭터의 직업이나 유형
스탯 | Stats | 캐릭터의 능력치
스킬 트리 | Skill Tree | 스킬 습득 체계
리롤 | Reroll | 캐릭터를 다시 만드는 것
커스터마이징 | Customization | 캐릭터 외형 변경
아바타 | Avatar | 플레이어를 대표하는 캐릭터
닉네임 | Nickname | 게임 내 사용자 이름

# 게임 플레이 용어
파밍 | Farming | 아이템이나 경험치를 반복적으로 획득하는 것
그라인딩 | Grinding | 반복적인 작업을 통한 성장
스피드런 | Speedrun | 최단 시간 내 게임 클리어
솔로 플레이 | Solo Play | 혼자서 게임하는 것
멀티 플레이 | Multiplayer | 여러 명이 함께 게임하는 것
랭킹 | Ranking | 순위
리더보드 | Leaderboard | 순위표
토너먼트 | Tournament | 경기 대회
시즌 | Season | 게임의 특정 기간
이벤트 | Event | 특별한 게임 내 행사

# 온라인 게임 용어
매치메이킹 | Matchmaking | 비슷한 실력의 플레이어끼리 매칭
로비 | Lobby | 게임 시작 전 대기실
방 만들기 | Create Room | 게임방 생성
방 참가 | Join Room | 게임방 입장
킥 | Kick | 플레이어를 강제로 내보내는 것
밴 | Ban | 계정 정지
신고 | Report | 부정행위나 욕설 신고
채팅 | Chat | 텍스트로 대화하는 것
음성 채팅 | Voice Chat | 음성으로 대화하는 것
친구 추가 | Add Friend | 친구 목록에 추가

# 모바일 게임 용어
가챠 | Gacha | 랜덤 뽑기 시스템
뽑기 | Draw/Pull | 랜덤으로 아이템이나 캐릭터 획득
과금 | In-app Purchase | 게임 내 결제
무과금 | Free-to-play | 돈을 쓰지 않고 게임하는 것
소과금 | Light Spender | 적은 금액만 결제하는 것
중과금 | Medium Spender | 중간 정도 금액을 결제하는 것
고과금 | Heavy Spender | 많은 금액을 결제하는 것
일일 미션 | Daily Mission | 매일 수행할 수 있는 임무
주간 미션 | Weekly Mission | 매주 수행할 수 있는 임무
출석 체크 | Daily Check-in | 매일 접속 보상
스태미나 | Stamina | 게임 플레이를 위한 에너지

# CS 관련 용어
고객 지원 | Customer Support | 고객 서비스
문의 | Inquiry | 질문이나 요청
신고 | Report | 문제 상황 알림
환불 | Refund | 결제 취소 및 돈 돌려받기
계정 복구 | Account Recovery | 잃어버린 계정 되찾기
비밀번호 재설정 | Password Reset | 비밀번호 변경
로그인 문제 | Login Issue | 접속 관련 문제
결제 문제 | Payment Issue | 결제 관련 문제
게임 오류 | Game Error | 게임 실행 중 발생하는 문제
연결 문제 | Connection Issue | 네트워크 연결 문제"""
    
    # 디버깅 정보 출력
    print(f"=== 하드코딩된 단어장 로드 ===")
    print(f"단어장 크기: {len(glossary)} 문자")
    print(f"Paul 포함 여부: {'Paul' in glossary}")
    print(f"Hogan 포함 여부: {'Hogan' in glossary}")
    print(f"Manuel 포함 여부: {'Manuel' in glossary}")
    print(f"Agent C 포함 여부: {'Agent C' in glossary}")
    print("=" * 30)
    
    return glossary

# 번역 관련 함수들
def create_translation_prompt_prefix():
    """번역을 위한 프롬프트 prefix 생성 (캐싱용)"""
    glossary = get_game_glossary()  # 하드코딩된 단어장 사용
    
    prefix = f"""You are a professional real-time chat translator specializing in gaming and customer service terminology. 
Your mission is to translate messages between Korean and English while maintaining gaming context and customer service tone.

## Your Role and Expertise
- Expert gaming translator with deep knowledge of gaming terminology
- Customer service specialist familiar with CS communication patterns
- Cultural bridge helping global gamers communicate effectively
- Maintain professional yet friendly tone appropriate for customer service

## Translation Guidelines
1. **Gaming Context Priority**: Always prioritize gaming-specific meanings over general translations
2. **Customer Service Tone**: Maintain professional, helpful, and friendly tone
3. **Cultural Adaptation**: Adapt expressions to be natural in target language
4. **Consistency**: Use consistent terminology throughout conversations
5. **Clarity**: Ensure translations are clear and unambiguous

## Game Terminology Glossary (CRITICAL - Use this for character and term recognition)
{glossary}

## Special Instructions
- For Korean to English: Use natural English expressions that English-speaking gamers would use
- For English to Korean: Use Korean gaming terminology that Korean gamers are familiar with
- Preserve emotional tone and urgency level of the original message
- If uncertain about gaming terms, use the most commonly accepted translation
- For customer service contexts, maintain professional courtesy markers
- Always use the glossary above for accurate gaming terminology translation

## Output Format Requirements
- Provide only the translated text
- Maintain natural flow in the target language
- Use appropriate gaming terminology from the glossary

"""
    return prefix

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
    """Nova Pro를 사용한 번역 함수 (Nova 전용 프롬프트 캐싱)"""
    
    # 언어 감지 및 타겟 언어 설정
    if target_language == "auto":
        # 간단한 언어 감지 (한글 포함 여부로 판단)
        if re.search(r'[가-힣]', text):
            target_language = "English"
            detected_language = "Korean"
        else:
            target_language = "Korean"
            detected_language = "English"
    else:
        detected_language = "Korean" if target_language == "English" else "English"
    
    # Prefix (캐싱될 부분) - 단어장 포함
    prefix_prompt = create_translation_prompt_prefix()
    
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
        
        response = clients['bedrock'].invoke_model(
            body=json.dumps(body),
            modelId='amazon.nova-pro-v1:0',
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        translated_content = response_body['output']['message']['content'][0]['text'].strip()
        
        # 토큰 사용량 로깅
        log_token_usage('amazon.nova-pro-v1:0', response_body, f"번역({target_language})")
        
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
        print(f"번역 API 호출 오류: {e}")
        # 오류 시 원본 텍스트 반환
        return {
            "original_text": text,
            "detected_language": detected_language,
            "target_language": target_language,
            "translated_text": text
        }



def extract_keywords(query):
    """쿼리에서 키워드 추출 - 개선된 버전"""
    # 불용어 제거
    stop_words = {'에', '대해', '대해서', '에서', '를', '을', '가', '이', '은', '는', '의', '와', '과', '로', '으로', '에게', '한테', '께', '부터', '까지', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'how', 'what', 'when', 'where', 'why', 'who'}
    
    # 조사 제거를 위한 패턴
    query_cleaned = re.sub(r'(에서|에게|에|를|을|가|이|은|는|의|와|과|로|으로|한테|께|부터|까지)(?=\s|$)', '', query)
    
    # 특수문자 제거 및 단어 분리
    words = re.findall(r'\b\w+\b', query_cleaned.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 1]
    
    # 추가로 원본 쿼리에서도 키워드 추출
    original_words = re.findall(r'\b\w+\b', query.lower())
    for word in original_words:
        if word not in stop_words and len(word) > 1 and word not in keywords:
            keywords.append(word)
    
    return list(set(keywords))  # 중복 제거

def search_knowledge_base(query, max_results=5):
    """Bedrock Knowledge Base에서 문서 검색"""
    try:
        # Bedrock Agent Runtime 클라이언트
        bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        response = bedrock_agent_client.retrieve(
            knowledgeBaseId='SJJP9YYPHX',
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results
                }
            }
        )
        
        results = []
        for result in response.get('retrievalResults', []):
            content = result.get('content', {}).get('text', '')
            score = result.get('score', 0)
            location = result.get('location', {})
            
            # S3 location에서 제목 추출 시도
            title = "Knowledge Base Document"
            if 's3Location' in location:
                s3_uri = location['s3Location'].get('uri', '')
                if s3_uri:
                    # S3 URI에서 파일명 추출하여 제목으로 사용
                    title = s3_uri.split('/')[-1].replace('.json', '').replace('.txt', '').replace('_', ' ')
            
            results.append({
                'title': title,
                'content': content,
                'url': location.get('s3Location', {}).get('uri', '#'),
                'score': score,
                'matched_keywords': []  # Knowledge Base는 벡터 검색으로 관련성 자동 계산
            })
        
        return results
        
    except Exception as e:
        print(f"Knowledge Base 검색 중 오류: {e}")
        st.error(f"Knowledge Base 검색 중 오류: {e}")
        return []

def create_answer_prompt_prefix(user_language="Korean"):
    """답변 생성을 위한 프롬프트 prefix 생성 (캐싱용)"""
    glossary = get_game_glossary()  # 하드코딩된 단어장 사용
    
    # 단어장 로드 상태 디버깅
    print(f"=== 답변 프롬프트 생성 디버깅 ===")
    print(f"언어: {user_language}")
    print(f"단어장 크기: {len(glossary)} 문자")
    print(f"Paul 포함: {'Paul' in glossary}")
    print(f"Hogan 포함: {'Hogan' in glossary}")
    print(f"Manuel 포함: {'Manuel' in glossary}")
    print(f"Agent C 포함: {'Agent C' in glossary}")
    print("=" * 40)
    
    if user_language == "English":
        prefix = f"""You are a professional Global Customer Service AI assistant specializing in gaming support and technical assistance.
Your mission is to provide accurate, helpful, and friendly customer service responses based on provided documentation.

## Your Role and Expertise
- Expert gaming customer service representative with deep knowledge of gaming terminology
- Technical support specialist familiar with troubleshooting and problem-solving
- Professional communicator maintaining friendly yet informative tone
- Cultural bridge helping global gamers with their inquiries

## Game Terminology Glossary (CRITICAL - Use this for character and term recognition)
{glossary}

## Response Guidelines
1. **Accuracy First**: Base all answers strictly on provided documentation
2. **Gaming Context**: Always prioritize gaming-specific meanings and context
3. **Professional Tone**: Maintain helpful, friendly, and professional customer service tone
4. **Clarity**: Provide clear, step-by-step explanations when needed
5. **Completeness**: Address all aspects of the user's question
6. **Consistency**: Use consistent terminology throughout responses

## Special Instructions
- Always use the glossary above for accurate character and term recognition
- For technical issues, provide systematic troubleshooting steps
- For game features, explain benefits and usage clearly
- Always maintain a helpful customer service attitude
- Use the glossary terms consistently throughout your response

"""
    else:
        prefix = f"""당신은 게임 지원 및 기술 지원을 전문으로 하는 글로벌 고객 서비스 AI 어시스턴트입니다.
제공된 문서를 바탕으로 정확하고 도움이 되는 친근한 고객 서비스 응답을 제공하는 것이 당신의 임무입니다.

## 당신의 역할과 전문성
- 게임 용어에 대한 깊은 지식을 가진 전문 게임 고객 서비스 담당자
- 문제 해결과 트러블슈팅에 익숙한 기술 지원 전문가
- 친근하면서도 정보를 제공하는 톤을 유지하는 전문 커뮤니케이터
- 전 세계 게이머들의 문의를 도와주는 문화적 가교 역할

## 게임 용어 단어장 (중요 - 캐릭터 및 용어 인식에 사용)
{glossary}

## 응답 가이드라인
1. **정확성 우선**: 제공된 문서를 바탕으로 모든 답변을 정확하게 작성
2. **게임 맥락**: 항상 게임 특화 의미와 맥락을 우선시
3. **전문적 톤**: 도움이 되고 친근하며 전문적인 고객 서비스 톤 유지
4. **명확성**: 필요시 명확하고 단계별 설명 제공
5. **완전성**: 사용자 질문의 모든 측면을 다룸
6. **일관성**: 응답 전반에 걸쳐 일관된 용어 사용

## 특별 지시사항
- 위의 게임 용어 단어장을 활용하여 정확한 캐릭터 및 용어 인식
- 기술적 문제의 경우 체계적인 문제 해결 단계 제공
- 게임 기능의 경우 장점과 사용법을 명확히 설명
- 항상 도움이 되는 고객 서비스 태도 유지
- 응답 전반에 걸쳐 단어장의 용어를 일관되게 사용

"""
    return prefix

def create_prompts(user_query, context_docs, conversation_history, user_language="Korean"):
    """각 모델에 맞는 프롬프트 생성 (다국어 지원, 캐싱 최적화)"""
    
    # 캐싱 가능한 prefix 생성
    cached_prefix = create_answer_prompt_prefix(user_language)
    
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

def stream_nova_model(model_id, prompt, max_tokens=500, temperature=0.3):
    """Nova 모델 스트리밍 호출 (Nova 전용 프롬프트 캐싱)"""
    
    # 프롬프트를 캐싱 가능한 부분과 동적 부분으로 분리
    lines = prompt.split('\n')
    
    # 캐싱 경계 찾기 (더 정확한 감지)
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
    
    if cache_boundary > 3:  # 최소 캐싱 조건 완화 (5 → 3)
        # 캐싱 가능한 부분 (단어장 + 시스템 지시사항)
        cached_content = '\n'.join(lines[:cache_boundary])
        
        # 디버깅: 캐싱 정보 출력
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

    body = {
        "messages": messages,
        "inferenceConfig": {
            "max_new_tokens": max_tokens,
            "temperature": temperature
        }
    }

    try:
        response = clients['bedrock'].invoke_model_with_response_stream(
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
                    
                    # 메타데이터에서 토큰 사용량 정보 추출 (스트리밍 완료 시)
                    if 'messageStop' in chunk_obj:
                        metadata = chunk_obj.get('messageStop', {})
                        if 'stopReason' in metadata:
                            print(f"스트리밍 완료: {metadata.get('stopReason')}")
                            
    except Exception as e:
        yield f"❌ {model_id} 스트리밍 오류: {e}"

def generate_dual_language_response(query, context_docs, conversation_history, 
                                   micro_prompt_ko, pro_prompt_ko, 
                                   micro_prompt_en, pro_prompt_en):
    """영어 사용자를 위한 이중 언어 답변 생성 - GitHub 원본 방식 완전 적용"""
    
    # 응답을 저장할 컨테이너
    response_container = st.empty()
    
    # 1단계: 한국어 답변 생성 (GitHub 원본과 동일한 병렬 실행)
    st.caption("🇰🇷 한국어 답변 생성 중 (담당자 확인용) - GitHub 원본 방식 병렬 처리...")
    
    # Pro 모델의 스트리밍 결과를 저장할 버퍼 (GitHub 원본과 동일)
    korean_pro_buffer = []
    korean_pro_complete = False
    
    def collect_korean_pro_stream():
        """한국어 Pro 모델의 스트리밍 결과를 버퍼에 수집 (GitHub 원본과 동일)"""
        nonlocal korean_pro_buffer, korean_pro_complete
        try:
            for chunk in stream_nova_model('amazon.nova-pro-v1:0', pro_prompt_ko, max_tokens=2048, temperature=0.5):
                korean_pro_buffer.append(chunk)
            korean_pro_complete = True
        except Exception as e:
            korean_pro_buffer.append(f"\n❌ Nova Pro (한국어) 오류: {e}")
            korean_pro_complete = True
    
    # GitHub 원본과 동일한 ThreadPoolExecutor 병렬 실행
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Pro 모델을 백그라운드에서 시작 (GitHub 원본과 동일)
        future_korean_pro = executor.submit(collect_korean_pro_stream)
        
        # 1단계: Nova Micro 스트리밍 (GitHub 원본과 동일한 실시간 출력)
        korean_micro_response = ""
        try:
            for chunk in stream_nova_model('amazon.nova-micro-v1:0', micro_prompt_ko, max_tokens=1024, temperature=0.3):
                korean_micro_response += chunk
                temp_display = f"## 📋 한국어 답변 (담당자 확인용)\n{korean_micro_response}▌"
                response_container.markdown(temp_display)
                time.sleep(0.02)  # GitHub 원본과 동일한 타이핑 효과
            
            # Micro 완료 후 최종 표시 (GitHub 원본과 동일)
            response_container.markdown(f"## 📋 한국어 답변 (담당자 확인용)\n{korean_micro_response}")
            
        except Exception as e:
            error_msg = f"❌ Nova Micro (한국어) 오류: {e}\n\n"
            korean_micro_response += error_msg
            response_container.markdown(f"## 📋 한국어 답변 (담당자 확인용)\n{korean_micro_response}")
        
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
        """영어 Pro 모델의 스트리밍 결과를 버퍼에 수집 (GitHub 원본과 동일)"""
        nonlocal english_pro_buffer, english_pro_complete
        try:
            for chunk in stream_nova_model('amazon.nova-pro-v1:0', pro_prompt_en, max_tokens=2048, temperature=0.5):
                english_pro_buffer.append(chunk)
            english_pro_complete = True
        except Exception as e:
            english_pro_buffer.append(f"\n❌ Nova Pro (English) Error: {e}")
            english_pro_complete = True
    
    # GitHub 원본과 동일한 ThreadPoolExecutor 병렬 실행
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Pro 모델을 백그라운드에서 시작 (GitHub 원본과 동일)
        future_english_pro = executor.submit(collect_english_pro_stream)
        
        # 1단계: Nova Micro 스트리밍 (GitHub 원본과 동일한 실시간 출력)
        english_micro_response = ""
        try:
            for chunk in stream_nova_model('amazon.nova-micro-v1:0', micro_prompt_en, max_tokens=1024, temperature=0.3):
                english_micro_response += chunk
                temp_display = f"""{korean_final}

---

## 🌍 English Response (For Customer)
{english_micro_response}▌"""
                response_container.markdown(temp_display)
                time.sleep(0.02)  # GitHub 원본과 동일한 타이핑 효과
            
            # Micro 완료 후 최종 표시 (GitHub 원본과 동일)
            temp_display = f"""{korean_final}

---

## 🌍 English Response (For Customer)
{english_micro_response}"""
            response_container.markdown(temp_display)
            
        except Exception as e:
            error_msg = f"❌ Nova Micro (English) Error: {e}\n\n"
            english_micro_response += error_msg
            temp_display = f"""{korean_final}

---

## 🌍 English Response (For Customer)
{english_micro_response}"""
            response_container.markdown(temp_display)
        
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

def generate_dual_answer(query, context_docs, conversation_history, user_language="Korean"):
    """듀얼 모델을 사용한 답변 생성 (완전한 다국어 지원)"""
    
    if not context_docs:
        if user_language == "English":
            return "Sorry, I couldn't find relevant documents. Please try searching with different keywords or rephrase your question."
        else:
            return "죄송합니다. 관련된 문서를 찾을 수 없습니다. 다른 키워드로 검색해보시거나 질문을 다시 작성해주세요."
    
    # 사용자 언어에 따라 프롬프트 생성
    if user_language == "English":
        # 영어 사용자: 한국어 답변 + 영어 답변 모두 생성
        # 1단계: 한국어로 답변 생성 (담당자 확인용)
        micro_prompt_ko, pro_prompt_ko = create_prompts(query, context_docs, conversation_history, "Korean")
        
        # 2단계: 영어로 답변 생성 (고객용)
        micro_prompt_en, pro_prompt_en = create_prompts(query, context_docs, conversation_history, "English")
        
        return generate_dual_language_response(query, context_docs, conversation_history, 
                                             micro_prompt_ko, pro_prompt_ko, 
                                             micro_prompt_en, pro_prompt_en)
    else:
        # 한국어 사용자: GitHub 원본과 100% 동일한 병렬 실행
        micro_prompt, pro_prompt = create_prompts(query, context_docs, conversation_history, "Korean")
        
        # 응답을 저장할 컨테이너
        response_container = st.empty()
        
        # Pro 모델의 스트리밍 결과를 저장할 버퍼 (GitHub 원본과 동일)
        pro_buffer = []
        pro_complete = False
        
        def collect_pro_stream():
            """Pro 모델의 스트리밍 결과를 버퍼에 수집 (GitHub 원본과 동일)"""
            nonlocal pro_buffer, pro_complete
            try:
                for chunk in stream_nova_model('amazon.nova-pro-v1:0', pro_prompt, max_tokens=2048, temperature=0.5):
                    pro_buffer.append(chunk)
                pro_complete = True
            except Exception as e:
                pro_buffer.append(f"\n❌ Nova Pro 오류: {e}")
                pro_complete = True
        
        # GitHub 원본과 동일한 ThreadPoolExecutor 병렬 실행
        with ThreadPoolExecutor(max_workers=2) as executor:
            st.caption("🚀 GitHub 원본 방식: Nova Micro + Pro 병렬 실행...")
            
            # Pro 모델을 백그라운드에서 시작 (GitHub 원본과 동일)
            future_pro = executor.submit(collect_pro_stream)
            
            # 1단계: Nova Micro 스트리밍 (GitHub 원본과 동일한 실시간 출력)
            full_micro_response = ""
            try:
                for chunk in stream_nova_model('amazon.nova-micro-v1:0', micro_prompt, max_tokens=1024, temperature=0.3):
                    full_micro_response += chunk
                    response_container.markdown(full_micro_response + "▌")
                    time.sleep(0.02)  # GitHub 원본과 동일한 타이핑 효과
                
                # Micro 완료 후 최종 표시 (GitHub 원본과 동일)
                response_container.markdown(full_micro_response)
                
            except Exception as e:
                error_msg = f"❌ Nova Micro 오류: {e}\n\n"
                full_micro_response += error_msg
                response_container.markdown(full_micro_response)
            
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
        # 최근 1시간 Nova Pro 토큰 사용량
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        response = boto3.client('cloudwatch', region_name='us-east-1').get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='InputTokenCount',
            Dimensions=[{'Name': 'ModelId', 'Value': 'amazon.nova-pro-v1:0'}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        if response['Datapoints']:
            input_tokens = int(response['Datapoints'][0]['Sum'])
            st.metric("Nova Pro 입력 토큰 (1시간)", f"{input_tokens:,}")
        else:
            st.info("토큰 사용량 데이터 없음")
            
        # 캐시 효율성 확인
        cache_response = boto3.client('cloudwatch', region_name='us-east-1').get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='CacheReadInputTokenCount',
            Dimensions=[{'Name': 'ModelId', 'Value': 'amazon.nova-pro-v1:0'}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        if cache_response['Datapoints']:
            cache_tokens = int(cache_response['Datapoints'][0]['Sum'])
            if input_tokens > 0:
                cache_efficiency = (cache_tokens / input_tokens) * 100
                st.metric("캐시 효율", f"{cache_efficiency:.1f}%", f"{cache_tokens:,} 토큰 절약")
            else:
                st.metric("캐시 토큰", f"{cache_tokens:,}")
        else:
            st.info("캐시 데이터 없음")
            
    except Exception as e:
        st.error(f"토큰 모니터링 오류: {str(e)[:50]}...")

    # 시스템 상태
    st.header("📊 시스템 상태")
    
    # Knowledge Base 상태 확인
    try:
        bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
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
