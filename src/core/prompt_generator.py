"""
프롬프트 생성 시스템 - 템플릿 패턴과 팩토리 패턴을 사용한 통합 프롬프트 생성

이 모듈은 기존의 중복된 프롬프트 생성 로직을 통합하여 
템플릿 패턴을 사용한 확장 가능한 프롬프트 생성 시스템을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.utils.glossary_manager import GlossaryManager


class BasePromptTemplate(ABC):
    """프롬프트 템플릿 기본 클래스
    
    템플릿 패턴을 사용하여 프롬프트 생성의 공통 구조를 정의하고,
    구체적인 프롬프트 타입별로 세부 구현을 위임합니다.
    """
    
    def __init__(self):
        self.glossary_manager = GlossaryManager()
    
    def create_prompt(self, **kwargs) -> str:
        """프롬프트 생성 메인 메서드 (템플릿 메서드)
        
        Args:
            **kwargs: 프롬프트 생성에 필요한 매개변수들
            
        Returns:
            str: 완성된 프롬프트 문자열
        """
        prefix = self.generate_prefix(**kwargs)
        suffix = self.generate_suffix(**kwargs)
        return f"{prefix}\n{suffix}" if suffix else prefix
    
    @abstractmethod
    def generate_prefix(self, **kwargs) -> str:
        """프롬프트 prefix 생성 (캐싱 가능한 부분)
        
        Args:
            **kwargs: 프롬프트 생성에 필요한 매개변수들
            
        Returns:
            str: 프롬프트 prefix 문자열
        """
        pass
    
    def generate_suffix(self, **kwargs) -> str:
        """프롬프트 suffix 생성 (동적 부분)
        
        기본적으로는 빈 문자열을 반환하며, 필요한 경우 하위 클래스에서 오버라이드
        
        Args:
            **kwargs: 프롬프트 생성에 필요한 매개변수들
            
        Returns:
            str: 프롬프트 suffix 문자열
        """
        return ""
    
    def _get_glossary(self) -> str:
        """게임 용어 단어장 가져오기
        
        Returns:
            str: 게임 용어 단어장 문자열
        """
        return self.glossary_manager.get_formatted_glossary()


class TranslationPromptTemplate(BasePromptTemplate):
    """번역용 프롬프트 템플릿
    
    게임 및 고객 서비스 용어 번역에 특화된 프롬프트를 생성합니다.
    """
    
    def generate_prefix(self, **kwargs) -> str:
        """번역용 프롬프트 prefix 생성
        
        Returns:
            str: 번역용 프롬프트 prefix
        """
        glossary = self._get_glossary()
        
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


class AnswerPromptTemplate(BasePromptTemplate):
    """답변 생성용 프롬프트 템플릿
    
    게임 고객 서비스 답변 생성에 특화된 프롬프트를 생성합니다.
    언어별로 다른 프롬프트를 제공합니다.
    """
    
    def generate_prefix(self, user_language: str = "Korean", **kwargs) -> str:
        """답변 생성용 프롬프트 prefix 생성
        
        Args:
            user_language: 사용자 언어 ("Korean" 또는 "English")
            **kwargs: 추가 매개변수들
            
        Returns:
            str: 답변 생성용 프롬프트 prefix
        """
        glossary = self._get_glossary()
        
        if user_language == "English":
            return self._generate_english_prefix(glossary)
        else:
            return self._generate_korean_prefix(glossary)
    
    def _generate_english_prefix(self, glossary: str) -> str:
        """영어 답변용 프롬프트 prefix 생성
        
        Args:
            glossary: 게임 용어 단어장
            
        Returns:
            str: 영어 답변용 프롬프트 prefix
        """
        return f"""You are a professional Global Customer Service AI assistant specializing in gaming support and technical assistance.
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
    
    def _generate_korean_prefix(self, glossary: str) -> str:
        """한국어 답변용 프롬프트 prefix 생성
        
        Args:
            glossary: 게임 용어 단어장
            
        Returns:
            str: 한국어 답변용 프롬프트 prefix
        """
        return f"""당신은 게임 지원 및 기술 지원을 전문으로 하는 글로벌 고객 서비스 AI 어시스턴트입니다.
제공된 문서를 바탕으로 정확하고 도움이 되는 친근한 고객 서비스 응답을 제공하는 것이 당신의 임무입니다.

## 당신의 역할과 전문성
- 게임 용어에 대한 깊은 지식을 가진 전문 게임 고객 서비스 담당자
- 문제 해결과 트러블슈팅에 익숙한 기술 지원 전문가
- 친근하면서도 정보를 제공하는 톤을 유지하는 전문 커뮤니케이터
- 전 세계 게이머들의 문의를 도와주는 문화적 가교 역할

## 게임 용어 단어장 (중요 - 캐릭터 및 용어 인식에 사용)
{glossary}

## 응답 가이드라인
1. **정확성 우선**: 제공된 문서를 바탕으로 모든 답변을 작성
2. **게임 맥락**: 항상 게임별 의미와 맥락을 우선시
3. **전문적 톤**: 도움이 되고 친근하며 전문적인 고객 서비스 톤 유지
4. **명확성**: 필요시 명확하고 단계별 설명 제공
5. **완전성**: 사용자 질문의 모든 측면을 다룸
6. **일관성**: 응답 전반에 걸쳐 일관된 용어 사용

## 특별 지침
- 캐릭터 및 용어 인식을 위해 항상 위의 단어장을 사용
- 기술적 문제의 경우 체계적인 문제 해결 단계 제공
- 게임 기능의 경우 이점과 사용법을 명확히 설명
- 항상 도움이 되는 고객 서비스 태도 유지
- 응답 전반에 걸쳐 단어장 용어를 일관되게 사용

"""


class PromptFactory:
    """프롬프트 생성 팩토리 클래스
    
    프롬프트 타입에 따라 적절한 템플릿을 선택하고 프롬프트를 생성합니다.
    기존의 create_translation_prompt_prefix()와 create_answer_prompt_prefix() 함수를 통합합니다.
    """
    
    # 프롬프트 타입별 템플릿 매핑
    _templates = {
        'translation': TranslationPromptTemplate,
        'answer': AnswerPromptTemplate,
    }
    
    @classmethod
    def create_prompt(cls, prompt_type: str, **kwargs) -> str:
        """프롬프트 생성
        
        Args:
            prompt_type: 프롬프트 타입 ('translation' 또는 'answer')
            **kwargs: 프롬프트 생성에 필요한 매개변수들
            
        Returns:
            str: 생성된 프롬프트 문자열
            
        Raises:
            ValueError: 지원하지 않는 프롬프트 타입인 경우
        """
        if prompt_type not in cls._templates:
            raise ValueError(f"지원하지 않는 프롬프트 타입: {prompt_type}. "
                           f"지원되는 타입: {list(cls._templates.keys())}")
        
        template_class = cls._templates[prompt_type]
        template = template_class()
        return template.create_prompt(**kwargs)
    
    @classmethod
    def create_translation_prompt(cls) -> str:
        """번역용 프롬프트 생성 (기존 create_translation_prompt_prefix 대체)
        
        Returns:
            str: 번역용 프롬프트
        """
        return cls.create_prompt('translation')
    
    @classmethod
    def create_answer_prompt(cls, user_language: str = "Korean") -> str:
        """답변 생성용 프롬프트 생성 (기존 create_answer_prompt_prefix 대체)
        
        Args:
            user_language: 사용자 언어 ("Korean" 또는 "English")
            
        Returns:
            str: 답변 생성용 프롬프트
        """
        return cls.create_prompt('answer', user_language=user_language)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """지원되는 프롬프트 타입 목록 반환
        
        Returns:
            list: 지원되는 프롬프트 타입 목록
        """
        return list(cls._templates.keys())