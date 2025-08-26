"""
게임 용어 단어장 관리 모듈

이 모듈은 게임 용어 단어장을 중앙화하여 관리하는 GlossaryManager 클래스를 제공합니다.
외부 JSON 파일에서 단어장을 로드하고, 실패 시 하드코딩된 fallback을 사용합니다.
"""

import json
import os
from typing import Dict, Any, Optional, List
import logging

# 로깅 설정
logger = logging.getLogger(__name__)


class GlossaryManager:
    """게임 용어 단어장 관리자
    
    config/game_glossary.json 파일에서 단어장을 로드하고,
    실패 시 하드코딩된 fallback 단어장을 사용합니다.
    """
    
    def __init__(self, config_path: str = "config/game_glossary.json"):
        """GlossaryManager 초기화
        
        Args:
            config_path: 게임 용어 단어장 JSON 파일 경로
        """
        self.config_path = config_path
        self._glossary_cache: Optional[Dict[str, Any]] = None
        self._formatted_glossary_cache: Optional[str] = None
        
    def load_glossary(self) -> Dict[str, Any]:
        """게임 용어 단어장을 로드합니다.
        
        먼저 외부 JSON 파일에서 로드를 시도하고,
        실패 시 하드코딩된 fallback 단어장을 반환합니다.
        
        Returns:
            Dict[str, Any]: 게임 용어 단어장 딕셔너리
        """
        # 캐시된 단어장이 있으면 반환
        if self._glossary_cache is not None:
            return self._glossary_cache
            
        try:
            # 외부 JSON 파일에서 로드 시도
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    glossary_data = json.load(f)
                
                # 단어장 검증
                if self.validate_glossary(glossary_data):
                    logger.info(f"게임 용어 단어장을 성공적으로 로드했습니다: {self.config_path}")
                    self._glossary_cache = glossary_data
                    return glossary_data
                else:
                    logger.warning(f"단어장 검증 실패, fallback 사용: {self.config_path}")
            else:
                logger.warning(f"단어장 파일이 존재하지 않음, fallback 사용: {self.config_path}")
                
        except Exception as e:
            logger.error(f"단어장 로드 중 오류 발생, fallback 사용: {e}")
        
        # fallback 단어장 사용
        fallback_glossary = self._get_fallback_glossary()
        self._glossary_cache = fallback_glossary
        return fallback_glossary
    
    def get_formatted_glossary(self) -> str:
        """프롬프트에 사용할 수 있는 형식으로 단어장을 반환합니다.
        
        Returns:
            str: 프롬프트용 형식화된 단어장 문자열
        """
        # 캐시된 형식화된 단어장이 있으면 반환
        if self._formatted_glossary_cache is not None:
            return self._formatted_glossary_cache
            
        glossary_data = self.load_glossary()
        formatted_text = self._format_glossary_for_prompt(glossary_data)
        self._formatted_glossary_cache = formatted_text
        return formatted_text
    
    def get_character_mapping(self) -> Dict[str, str]:
        """캐릭터 이름 매핑을 반환합니다.
        
        Returns:
            Dict[str, str]: 캐릭터 이름 매핑 (한국어 -> 영어)
        """
        glossary_data = self.load_glossary()
        
        # JSON 형식의 단어장인 경우
        if 'characters' in glossary_data:
            character_mapping = {}
            for eng_name, char_info in glossary_data['characters'].items():
                aliases = char_info.get('aliases', [])
                for alias in aliases:
                    character_mapping[alias] = eng_name
            return character_mapping
        
        # 기존 하드코딩 형식인 경우 (fallback)
        return self._extract_character_mapping_from_text()
    
    def get_term_translation(self, term: str, target_lang: str = "en") -> str:
        """특정 용어의 번역을 반환합니다.
        
        Args:
            term: 번역할 용어
            target_lang: 목표 언어 ("en" 또는 "ko")
            
        Returns:
            str: 번역된 용어 (찾지 못하면 원본 반환)
        """
        glossary_data = self.load_glossary()
        
        # JSON 형식의 단어장인 경우
        if isinstance(glossary_data, dict) and any(key in glossary_data for key in ['characters', 'items', 'locations']):
            return self._find_translation_in_json(glossary_data, term, target_lang)
        
        # 기존 텍스트 형식인 경우
        return self._find_translation_in_text(term, target_lang)
    
    def validate_glossary(self, glossary: Dict[str, Any]) -> bool:
        """단어장 데이터의 유효성을 검증합니다.
        
        Args:
            glossary: 검증할 단어장 딕셔너리
            
        Returns:
            bool: 유효성 검증 결과
        """
        try:
            # 기본 구조 검증
            if not isinstance(glossary, dict):
                logger.error("단어장이 딕셔너리 형식이 아닙니다")
                return False
            
            # JSON 형식 단어장 검증
            if any(key in glossary for key in ['characters', 'items', 'locations']):
                return self._validate_json_glossary(glossary)
            
            # 텍스트 형식 단어장 검증 (fallback)
            if isinstance(glossary, str):
                return len(glossary.strip()) > 0
            
            logger.warning("알 수 없는 단어장 형식")
            return False
            
        except Exception as e:
            logger.error(f"단어장 검증 중 오류: {e}")
            return False
    
    def reload_glossary(self) -> None:
        """단어장을 다시 로드합니다 (캐시 초기화)."""
        self._glossary_cache = None
        self._formatted_glossary_cache = None
        logger.info("단어장 캐시가 초기화되었습니다")    
    def _validate_json_glossary(self, glossary: Dict[str, Any]) -> bool:
        """JSON 형식 
단어장의 유효성을 검증합니다."""
        required_sections = ['characters', 'items', 'locations']
        
        for section in required_sections:
            if section in glossary:
                section_data = glossary[section]
                if not isinstance(section_data, dict):
                    logger.error(f"섹션 '{section}'이 딕셔너리 형식이 아닙니다")
                    return False
                
                # 각 항목 검증
                for key, value in section_data.items():
                    if not isinstance(value, dict):
                        logger.error(f"항목 '{key}'가 딕셔너리 형식이 아닙니다")
                        return False
                    
                    # 필수 필드 검증
                    if 'description' not in value:
                        logger.error(f"항목 '{key}'에 description이 없습니다")
                        return False
                    
                    if 'aliases' not in value or not isinstance(value['aliases'], list):
                        logger.error(f"항목 '{key}'에 유효한 aliases가 없습니다")
                        return False
        
        return True
    
    def _format_glossary_for_prompt(self, glossary_data: Dict[str, Any]) -> str:
        """단어장을 프롬프트용 텍스트 형식으로 변환합니다."""
        
        # JSON 형식인 경우
        if isinstance(glossary_data, dict) and any(key in glossary_data for key in ['characters', 'items', 'locations']):
            return self._format_json_glossary(glossary_data)
        
        # 이미 텍스트 형식인 경우 (fallback)
        if isinstance(glossary_data, str):
            return glossary_data
        
        # 기타 경우 fallback 사용
        return self._get_fallback_glossary_text()
    
    def _format_json_glossary(self, glossary_data: Dict[str, Any]) -> str:
        """JSON 형식 단어장을 프롬프트용 텍스트로 변환합니다."""
        formatted_lines = ["# 게임 용어 단어장 (한국어 <-> 영어)", "# 형식: 한국어 용어 | 영어 용어 | 설명", ""]
        
        # 섹션별 한국어 제목 매핑
        section_titles = {
            'characters': '# 캐릭터 이름',
            'game_terms': '# 기본 게임 용어',
            'combat_terms': '# 전투 관련 용어',
            'items': '# 아이템 관련 용어',
            'system_terms': '# 게임 시스템 용어',
            'character_terms': '# 캐릭터 관련 용어',
            'gameplay_terms': '# 게임 플레이 용어',
            'online_terms': '# 온라인 게임 용어',
            'mobile_terms': '# 모바일 게임 용어',
            'cs_terms': '# CS 관련 용어',
            'locations': '# 게임 위치'
        }
        
        # 모든 섹션 처리
        for section_name, section_data in glossary_data.items():
            if isinstance(section_data, dict) and section_name in section_titles:
                formatted_lines.append(section_titles[section_name])
                
                for eng_name, item_info in section_data.items():
                    description = item_info.get('description', '')
                    aliases = item_info.get('aliases', [])
                    
                    # 한국어 별명 찾기 (한글 유니코드 범위 확인)
                    korean_aliases = []
                    for alias in aliases:
                        if any('\u3131' <= c <= '\u3163' or '\uac00' <= c <= '\ud7a3' for c in alias):
                            korean_aliases.append(alias)
                    
                    korean_name = korean_aliases[0] if korean_aliases else eng_name
                    
                    formatted_lines.append(f"{korean_name} | {eng_name} | {description}")
                
                formatted_lines.append("")
        
        return "\n".join(formatted_lines)
    
    def _find_translation_in_json(self, glossary_data: Dict[str, Any], term: str, target_lang: str) -> str:
        """JSON 형식 단어장에서 용어 번역을 찾습니다."""
        for section_name, section_data in glossary_data.items():
            if isinstance(section_data, dict):
                for eng_name, item_info in section_data.items():
                    aliases = item_info.get('aliases', [])
                    
                    # 용어가 별명 목록에 있는지 확인
                    if term.lower() in [alias.lower() for alias in aliases]:
                        if target_lang == "en":
                            return eng_name
                        else:  # target_lang == "ko"
                            # 한국어 별명 찾기
                            korean_aliases = [alias for alias in aliases if any('\u3131' <= c <= '\u3163' or '\uac00' <= c <= '\ud7a3' for c in alias)]
                            return korean_aliases[0] if korean_aliases else eng_name
                    
                    # 영어 이름과 직접 매치
                    if term.lower() == eng_name.lower():
                        if target_lang == "en":
                            return eng_name
                        else:
                            korean_aliases = [alias for alias in aliases if any('\u3131' <= c <= '\u3163' or '\uac00' <= c <= '\ud7a3' for c in alias)]
                            return korean_aliases[0] if korean_aliases else eng_name
        
        return term  # 찾지 못하면 원본 반환
    
    def _find_translation_in_text(self, term: str, target_lang: str) -> str:
        """텍스트 형식 단어장에서 용어 번역을 찾습니다."""
        # 기존 하드코딩된 단어장에서 검색하는 로직
        # 이는 fallback 용도로만 사용됩니다
        return term  # 간단한 구현으로 원본 반환
    
    def _extract_character_mapping_from_text(self) -> Dict[str, str]:
        """텍스트 형식 단어장에서 캐릭터 매핑을 추출합니다."""
        # 기존 하드코딩된 형식에서 캐릭터 매핑 추출
        # 이는 fallback 용도로만 사용됩니다
        return {
            "주인공": "Paul",
            "폴": "Paul",
            "공대한": "Hogan", 
            "마누엘": "Manuel",
            "에이전트 C": "Agent C"
        }
    
    def _get_fallback_glossary(self) -> Dict[str, Any]:
        """하드코딩된 fallback 단어장을 반환합니다."""
        logger.info("Fallback 단어장을 사용합니다")
        
        # 기존 하드코딩된 단어장을 딕셔너리 형태로 반환
        return {
            "fallback_text": self._get_fallback_glossary_text(),
            "type": "fallback"
        }
    
    def _get_fallback_glossary_text(self) -> str:
        """하드코딩된 fallback 단어장 텍스트를 반환합니다."""
        return """# 게임 용어 단어장 (한국어 <-> 영어)
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


# 싱글톤 인스턴스 생성
_glossary_manager_instance: Optional[GlossaryManager] = None


def get_glossary_manager() -> GlossaryManager:
    """GlossaryManager 싱글톤 인스턴스를 반환합니다.
    
    Returns:
        GlossaryManager: 싱글톤 인스턴스
    """
    global _glossary_manager_instance
    if _glossary_manager_instance is None:
        _glossary_manager_instance = GlossaryManager()
    return _glossary_manager_instance