"""
GlossaryManager 단위 테스트

이 테스트는 GlossaryManager의 핵심 기능을 검증합니다:
- 외부 JSON 파일에서 단어장 로딩
- Fallback 메커니즘 동작
- 단어장 검증 기능
- 캐릭터 매핑 및 용어 번역
- 캐싱 메커니즘
"""

import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import sys

# 테스트를 위한 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.glossary_manager import GlossaryManager, get_glossary_manager


class TestGlossaryManager(unittest.TestCase):
    """GlossaryManager 테스트 클래스"""
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_glossary.json")
        
        # 테스트용 JSON 단어장 데이터
        self.test_glossary_data = {
            "characters": {
                "Paul": {
                    "description": "주인공 캐릭터",
                    "aliases": ["주인공", "폴", "Paul"]
                },
                "Hogan": {
                    "description": "게임 내 캐릭터 공대한",
                    "aliases": ["공대한", "Hogan"]
                }
            },
            "game_terms": {
                "Level Up": {
                    "description": "캐릭터의 레벨이 상승하는 것",
                    "aliases": ["레벨업", "Level Up"]
                },
                "Experience Points": {
                    "description": "캐릭터 성장을 위한 포인트",
                    "aliases": ["경험치", "XP", "Experience Points"]
                }
            }
        }
        
        # 싱글톤 인스턴스 초기화
        global _glossary_manager_instance
        import src.utils.glossary_manager
        src.utils.glossary_manager._glossary_manager_instance = None
    
    def tearDown(self):
        """각 테스트 후에 실행되는 정리"""
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # 싱글톤 인스턴스 초기화
        global _glossary_manager_instance
        import src.utils.glossary_manager
        src.utils.glossary_manager._glossary_manager_instance = None
    
    def test_load_glossary_from_file_success(self):
        """외부 JSON 파일에서 단어장 로딩 성공 테스트"""
        # 테스트 JSON 파일 생성
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_glossary_data, f, ensure_ascii=False, indent=2)
        
        manager = GlossaryManager(config_path=self.config_path)
        glossary = manager.load_glossary()
        
        # 로드된 데이터가 올바른지 확인
        self.assertEqual(glossary, self.test_glossary_data)
        self.assertIn("characters", glossary)
        self.assertIn("Paul", glossary["characters"])
        self.assertEqual(glossary["characters"]["Paul"]["aliases"], ["주인공", "폴", "Paul"])
    
    def test_load_glossary_file_not_exists(self):
        """파일이 존재하지 않을 때 fallback 사용 테스트"""
        non_existent_path = os.path.join(self.temp_dir, "non_existent.json")
        
        manager = GlossaryManager(config_path=non_existent_path)
        glossary = manager.load_glossary()
        
        # Fallback 단어장이 로드되어야 함
        self.assertIn("type", glossary)
        self.assertEqual(glossary["type"], "fallback")
        self.assertIn("fallback_text", glossary)
    
    def test_load_glossary_invalid_json(self):
        """잘못된 JSON 파일일 때 fallback 사용 테스트"""
        # 잘못된 JSON 파일 생성
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        
        manager = GlossaryManager(config_path=self.config_path)
        glossary = manager.load_glossary()
        
        # Fallback 단어장이 로드되어야 함
        self.assertIn("type", glossary)
        self.assertEqual(glossary["type"], "fallback")
    
    def test_load_glossary_validation_failure(self):
        """단어장 검증 실패 시 fallback 사용 테스트"""
        # 검증에 실패할 잘못된 구조의 JSON 생성
        invalid_data = {
            "characters": {
                "Paul": {
                    # description 누락
                    "aliases": ["주인공", "폴"]
                }
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        manager = GlossaryManager(config_path=self.config_path)
        glossary = manager.load_glossary()
        
        # Fallback 단어장이 로드되어야 함
        self.assertIn("type", glossary)
        self.assertEqual(glossary["type"], "fallback")
    
    def test_glossary_caching(self):
        """단어장 캐싱 메커니즘 테스트"""
        # 테스트 JSON 파일 생성
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_glossary_data, f)
        
        manager = GlossaryManager(config_path=self.config_path)
        
        # 첫 번째 로드
        glossary1 = manager.load_glossary()
        
        # 두 번째 로드 (캐시에서 가져와야 함)
        glossary2 = manager.load_glossary()
        
        # 같은 객체여야 함 (캐싱 확인)
        self.assertIs(glossary1, glossary2)
    
    def test_validate_glossary_valid_json(self):
        """유효한 JSON 단어장 검증 테스트"""
        manager = GlossaryManager()
        
        # 유효한 단어장
        valid_glossary = {
            "characters": {
                "Paul": {
                    "description": "주인공 캐릭터",
                    "aliases": ["주인공", "폴"]
                }
            }
        }
        
        result = manager.validate_glossary(valid_glossary)
        self.assertTrue(result)
    
    def test_validate_glossary_invalid_structure(self):
        """잘못된 구조의 단어장 검증 테스트"""
        manager = GlossaryManager()
        
        # 잘못된 구조들
        invalid_cases = [
            # 딕셔너리가 아닌 경우
            "not a dict",
            # description 누락
            {
                "characters": {
                    "Paul": {
                        "aliases": ["주인공"]
                    }
                }
            },
            # aliases가 리스트가 아닌 경우
            {
                "characters": {
                    "Paul": {
                        "description": "주인공",
                        "aliases": "not a list"
                    }
                }
            },
            # 섹션이 딕셔너리가 아닌 경우
            {
                "characters": "not a dict"
            }
        ]
        
        for invalid_glossary in invalid_cases:
            with self.subTest(invalid_glossary=invalid_glossary):
                result = manager.validate_glossary(invalid_glossary)
                self.assertFalse(result)
    
    def test_get_formatted_glossary(self):
        """형식화된 단어장 반환 테스트"""
        # 테스트 JSON 파일 생성
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_glossary_data, f)
        
        manager = GlossaryManager(config_path=self.config_path)
        formatted_text = manager.get_formatted_glossary()
        
        # 형식화된 텍스트에 필요한 내용이 포함되어야 함
        self.assertIn("# 게임 용어 단어장", formatted_text)
        self.assertIn("# 캐릭터 이름", formatted_text)
        self.assertIn("주인공 | Paul", formatted_text)
        self.assertIn("레벨업 | Level Up", formatted_text)
    
    def test_get_formatted_glossary_caching(self):
        """형식화된 단어장 캐싱 테스트"""
        # 테스트 JSON 파일 생성
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_glossary_data, f)
        
        manager = GlossaryManager(config_path=self.config_path)
        
        # 첫 번째 호출
        formatted1 = manager.get_formatted_glossary()
        
        # 두 번째 호출 (캐시에서 가져와야 함)
        formatted2 = manager.get_formatted_glossary()
        
        # 같은 문자열이어야 함
        self.assertEqual(formatted1, formatted2)
    
    def test_get_character_mapping(self):
        """캐릭터 매핑 반환 테스트"""
        # 테스트 JSON 파일 생성
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_glossary_data, f)
        
        manager = GlossaryManager(config_path=self.config_path)
        mapping = manager.get_character_mapping()
        
        # 캐릭터 매핑이 올바르게 생성되어야 함
        self.assertIn("주인공", mapping)
        self.assertIn("폴", mapping)
        self.assertIn("공대한", mapping)
        self.assertEqual(mapping["주인공"], "Paul")
        self.assertEqual(mapping["폴"], "Paul")
        self.assertEqual(mapping["공대한"], "Hogan")
    
    def test_get_character_mapping_fallback(self):
        """Fallback 단어장에서 캐릭터 매핑 테스트"""
        non_existent_path = os.path.join(self.temp_dir, "non_existent.json")
        
        manager = GlossaryManager(config_path=non_existent_path)
        mapping = manager.get_character_mapping()
        
        # Fallback 매핑이 반환되어야 함
        self.assertIsInstance(mapping, dict)
        self.assertIn("주인공", mapping)
        self.assertEqual(mapping["주인공"], "Paul")
    
    def test_get_term_translation_json_format(self):
        """JSON 형식 단어장에서 용어 번역 테스트"""
        # 테스트 JSON 파일 생성
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_glossary_data, f)
        
        manager = GlossaryManager(config_path=self.config_path)
        
        # 한국어 -> 영어 번역
        result = manager.get_term_translation("레벨업", "en")
        self.assertEqual(result, "Level Up")
        
        # 영어 -> 한국어 번역
        result = manager.get_term_translation("Level Up", "ko")
        self.assertEqual(result, "레벨업")
        
        # 존재하지 않는 용어
        result = manager.get_term_translation("존재하지않는용어", "en")
        self.assertEqual(result, "존재하지않는용어")
    
    def test_reload_glossary(self):
        """단어장 다시 로드 테스트"""
        # 테스트 JSON 파일 생성
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_glossary_data, f)
        
        manager = GlossaryManager(config_path=self.config_path)
        
        # 첫 번째 로드
        glossary1 = manager.load_glossary()
        formatted1 = manager.get_formatted_glossary()
        
        # 캐시 초기화
        manager.reload_glossary()
        
        # 다시 로드
        glossary2 = manager.load_glossary()
        formatted2 = manager.get_formatted_glossary()
        
        # 내용은 같지만 다른 객체여야 함 (다시 로드되었음을 의미)
        self.assertEqual(glossary1, glossary2)
        self.assertEqual(formatted1, formatted2)
        # 캐시가 초기화되었으므로 새로운 객체여야 함
        self.assertIsNot(glossary1, glossary2)
    
    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        manager1 = get_glossary_manager()
        manager2 = get_glossary_manager()
        
        # 같은 인스턴스여야 함
        self.assertIs(manager1, manager2)
    
    def test_fallback_glossary_content(self):
        """Fallback 단어장 내용 테스트"""
        non_existent_path = os.path.join(self.temp_dir, "non_existent.json")
        
        manager = GlossaryManager(config_path=non_existent_path)
        glossary = manager.load_glossary()
        
        # Fallback 단어장이어야 함
        self.assertEqual(glossary["type"], "fallback")
        
        # Fallback 텍스트에 기본 내용이 포함되어야 함
        fallback_text = glossary["fallback_text"]
        self.assertIn("게임 용어 단어장", fallback_text)
        self.assertIn("캐릭터 이름", fallback_text)
        self.assertIn("주인공 | Paul", fallback_text)
        self.assertIn("레벨업 | Level Up", fallback_text)
    
    @patch('src.utils.glossary_manager.logger')
    def test_logging_behavior(self, mock_logger):
        """로깅 동작 테스트"""
        # 성공적인 로딩
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_glossary_data, f)
        
        manager = GlossaryManager(config_path=self.config_path)
        manager.load_glossary()
        
        # 성공 로그가 기록되어야 함
        mock_logger.info.assert_called()
        
        # 파일이 없는 경우
        mock_logger.reset_mock()
        non_existent_path = os.path.join(self.temp_dir, "non_existent.json")
        manager2 = GlossaryManager(config_path=non_existent_path)
        manager2.load_glossary()
        
        # 경고 로그가 기록되어야 함
        mock_logger.warning.assert_called()


if __name__ == '__main__':
    unittest.main()