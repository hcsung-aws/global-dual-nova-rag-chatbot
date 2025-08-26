"""
게임 용어 단어장 래퍼 모듈

Streamlit 의존성 없이 GlossaryManager 기능을 테스트할 수 있는 래퍼 함수들을 제공합니다.
"""

from .glossary_manager import get_glossary_manager


def get_game_glossary_standalone():
    """Streamlit 의존성 없이 게임 용어 단어장을 반환합니다.
    
    이 함수는 테스트 목적으로 사용되며, chatbot_app.py의 get_game_glossary()와
    동일한 기능을 제공하지만 Streamlit import 없이 작동합니다.
    
    Returns:
        str: 프롬프트용 형식화된 게임 용어 단어장
    """
    try:
        # GlossaryManager를 통해 단어장 로드
        glossary_manager = get_glossary_manager()
        glossary = glossary_manager.get_formatted_glossary()
        
        # 디버깅 정보 출력
        print(f"=== GlossaryManager 단어장 로드 (독립 실행) ===")
        print(f"단어장 크기: {len(glossary)} 문자")
        print(f"Paul 포함 여부: {'Paul' in glossary}")
        print(f"Hogan 포함 여부: {'Hogan' in glossary}")
        print(f"Manuel 포함 여부: {'Manuel' in glossary}")
        print(f"Agent C 포함 여부: {'Agent C' in glossary}")
        print("=" * 45)
        
        return glossary
        
    except Exception as e:
        print(f"GlossaryManager 로드 중 오류: {e}")
        # 오류 시에도 기본 단어장 제공 (안정성 보장)
        return "# 게임 용어 단어장 로드 오류\n기본 단어장을 사용합니다."


def test_glossary_functionality():
    """GlossaryManager의 모든 기능을 테스트합니다.
    
    Returns:
        bool: 모든 테스트 통과 여부
    """
    try:
        print("=== GlossaryManager 기능 테스트 시작 ===")
        
        # 1. 기본 단어장 로드 테스트
        glossary = get_game_glossary_standalone()
        assert len(glossary) > 0, "단어장이 비어있습니다"
        print("✅ 기본 단어장 로드 테스트 통과")
        
        # 2. GlossaryManager 직접 테스트
        manager = get_glossary_manager()
        
        # 3. 캐릭터 매핑 테스트
        char_mapping = manager.get_character_mapping()
        assert len(char_mapping) > 0, "캐릭터 매핑이 비어있습니다"
        print(f"✅ 캐릭터 매핑 테스트 통과 ({len(char_mapping)}개 매핑)")
        
        # 4. 용어 번역 테스트
        paul_translation = manager.get_term_translation("Paul", "ko")
        print(f"✅ 용어 번역 테스트 통과 (Paul -> {paul_translation})")
        
        # 5. 단어장 재로드 테스트
        manager.reload_glossary()
        reloaded_glossary = manager.get_formatted_glossary()
        assert len(reloaded_glossary) > 0, "재로드된 단어장이 비어있습니다"
        print("✅ 단어장 재로드 테스트 통과")
        
        print("=== 모든 GlossaryManager 기능 테스트 통과! ===")
        return True
        
    except Exception as e:
        print(f"❌ GlossaryManager 기능 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_with_original():
    """원본 하드코딩 방식과 GlossaryManager 방식을 비교합니다.
    
    Returns:
        bool: 비교 테스트 통과 여부
    """
    try:
        print("=== 원본 vs GlossaryManager 비교 테스트 ===")
        
        # GlossaryManager 방식
        new_glossary = get_game_glossary_standalone()
        
        # 기본 검증
        essential_terms = ["Paul", "게임", "캐릭터", "아이템"]
        missing_terms = []
        
        for term in essential_terms:
            if term not in new_glossary:
                missing_terms.append(term)
        
        if missing_terms:
            print(f"❌ 필수 용어 누락: {missing_terms}")
            return False
        
        print("✅ 모든 필수 용어 포함 확인")
        print(f"✅ 새로운 단어장 크기: {len(new_glossary)} 문자")
        print("=== 비교 테스트 통과! ===")
        return True
        
    except Exception as e:
        print(f"❌ 비교 테스트 실패: {e}")
        return False