"""
ConfigManager 단위 테스트

ConfigManager 클래스의 기능을 검증하는 테스트 모음입니다.
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

from src.utils.config_manager import ConfigManager, get_config_manager, get_config, get_aws_config, get_setting
from src.config.models import AppConfig, AWSConfig, UIConfig, LoggingConfig, CacheConfig


class TestConfigManager(unittest.TestCase):
    """ConfigManager 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 싱글톤 인스턴스 초기화
        ConfigManager._instance = None
        ConfigManager._config = None
        ConfigManager._config_loaded = False
        
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """테스트 정리"""
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # 싱글톤 인스턴스 초기화
        ConfigManager._instance = None
        ConfigManager._config = None
        ConfigManager._config_loaded = False
    
    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        
        # 같은 인스턴스여야 함
        self.assertIs(manager1, manager2)
        
        # get_config_manager()로도 같은 인스턴스 반환
        manager3 = get_config_manager()
        self.assertIs(manager1, manager3)
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_default_config_loading(self, mock_get_paths):
        """기본 설정 로딩 테스트"""
        # 설정 파일이 없는 경우
        mock_get_paths.return_value = []
        
        manager = ConfigManager()
        config = manager.get_config()
        
        # 기본값들이 설정되어야 함
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.aws.region, "us-east-1")
        self.assertEqual(config.ui.page_title, "글로벌 CS 챗봇 🌍")
        self.assertEqual(config.logging.level, "INFO")
        self.assertTrue(config.cache.enabled)
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_config_file_loading(self, mock_get_paths):
        """설정 파일 로딩 테스트"""
        # 테스트 설정 파일 생성
        config_file = self.config_dir / "test.json"
        test_config = {
            "aws": {
                "region": "ap-northeast-2",
                "knowledge_base_id": "TEST_KB_ID"
            },
            "ui": {
                "page_title": "테스트 챗봇"
            },
            "environment": "test"
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        mock_get_paths.return_value = [config_file]
        
        manager = ConfigManager()
        config = manager.get_config()
        
        # 설정 파일의 값들이 적용되어야 함
        self.assertEqual(config.aws.region, "ap-northeast-2")
        self.assertEqual(config.aws.knowledge_base_id, "TEST_KB_ID")
        self.assertEqual(config.ui.page_title, "테스트 챗봇")
        self.assertEqual(config.environment, "test")
    
    @patch.dict(os.environ, {
        'AWS_DEFAULT_REGION': 'eu-west-1',
        'KNOWLEDGE_BASE_ID': 'ENV_KB_ID',
        'ENVIRONMENT': 'production',
        'DEBUG': 'true',
        'LOG_LEVEL': 'DEBUG'
    })
    @patch.object(ConfigManager, '_get_config_paths')
    def test_env_override(self, mock_get_paths):
        """환경 변수 오버라이드 테스트"""
        mock_get_paths.return_value = []
        
        manager = ConfigManager()
        config = manager.get_config()
        
        # 환경 변수 값들이 적용되어야 함
        self.assertEqual(config.aws.region, "eu-west-1")
        self.assertEqual(config.aws.knowledge_base_id, "ENV_KB_ID")
        self.assertEqual(config.environment, "production")
        self.assertTrue(config.debug)
        self.assertEqual(config.logging.level, "DEBUG")
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_get_setting_method(self, mock_get_paths):
        """get_setting 메서드 테스트"""
        mock_get_paths.return_value = []
        
        manager = ConfigManager()
        
        # 점 표기법으로 설정값 조회
        self.assertEqual(manager.get_setting('aws.region'), 'us-east-1')
        self.assertEqual(manager.get_setting('ui.page_title'), '글로벌 CS 챗봇 🌍')
        self.assertEqual(manager.get_setting('logging.level'), 'INFO')
        
        # 존재하지 않는 설정
        self.assertIsNone(manager.get_setting('nonexistent.setting'))
        self.assertEqual(manager.get_setting('nonexistent.setting', 'default'), 'default')
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_config_validation(self, mock_get_paths):
        """설정 검증 테스트"""
        # 잘못된 설정 파일 생성
        config_file = self.config_dir / "invalid.json"
        invalid_config = {
            "aws": {
                "region": "",  # 빈 region
                "knowledge_base_id": ""  # 빈 KB ID
            },
            "logging": {
                "level": "INVALID_LEVEL"  # 잘못된 로그 레벨
            },
            "environment": "invalid_env"  # 잘못된 환경
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_config, f)
        
        mock_get_paths.return_value = [config_file]
        
        # 검증 오류로 인해 예외가 발생해야 함
        with self.assertRaises(ValueError):
            ConfigManager()
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_validate_required_settings(self, mock_get_paths):
        """필수 설정 검증 테스트"""
        mock_get_paths.return_value = []
        
        manager = ConfigManager()
        
        # 기본 설정에서는 필수 설정이 모두 있어야 함
        missing = manager.validate_required_settings()
        self.assertEqual(len(missing), 0)
        
        # AWS region을 제거하고 테스트
        manager._config.aws.region = ""
        missing = manager.validate_required_settings()
        self.assertGreater(len(missing), 0)
        self.assertTrue(any("AWS region" in item for item in missing))
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_convenience_functions(self, mock_get_paths):
        """편의 함수들 테스트"""
        mock_get_paths.return_value = []
        
        # 전역 함수들이 올바르게 동작해야 함
        config = get_config()
        self.assertIsInstance(config, AppConfig)
        
        aws_config = get_aws_config()
        self.assertIsInstance(aws_config, AWSConfig)
        
        setting_value = get_setting('aws.region')
        self.assertEqual(setting_value, 'us-east-1')
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_config_summary(self, mock_get_paths):
        """설정 요약 정보 테스트"""
        mock_get_paths.return_value = []
        
        manager = ConfigManager()
        summary = manager.get_config_summary()
        
        # 요약 정보에 필요한 키들이 있어야 함
        expected_keys = [
            'environment', 'debug', 'aws_region', 
            'knowledge_base_id', 'ui_theme', 'logging_level', 'cache_enabled'
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        # 민감한 정보는 마스킹되어야 함
        if summary['knowledge_base_id']:
            self.assertTrue(summary['knowledge_base_id'].endswith('...'))
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_reload_config(self, mock_get_paths):
        """설정 다시 로드 테스트"""
        mock_get_paths.return_value = []
        
        manager = ConfigManager()
        original_config = manager.get_config()
        
        # 설정 다시 로드
        manager.reload_config()
        reloaded_config = manager.get_config()
        
        # 새로운 객체여야 함 (다시 로드되었음을 의미)
        self.assertIsNot(original_config, reloaded_config)
    
    @patch.object(ConfigManager, '_get_config_paths')
    def test_invalid_json_handling(self, mock_get_paths):
        """잘못된 JSON 파일 처리 테스트"""
        # 잘못된 JSON 파일 생성
        config_file = self.config_dir / "invalid.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        
        mock_get_paths.return_value = [config_file]
        
        # JSON 파싱 오류로 인해 예외가 발생해야 함
        with self.assertRaises(json.JSONDecodeError):
            ConfigManager()


if __name__ == '__main__':
    unittest.main()