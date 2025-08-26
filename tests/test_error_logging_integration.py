"""
에러 처리 및 로깅 시스템 통합 테스트

이 테스트는 새로운 표준화된 에러 처리 및 로깅 시스템이 
올바르게 작동하는지 검증합니다.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.error_handler import (
    ErrorHandler, StandardError, ErrorSeverity, ErrorCategory, get_error_handler
)
from src.utils.logger import StandardLogger, get_logger, setup_logging_from_config
from src.utils.error_logging_utils import (
    handle_errors, log_performance, error_context, performance_context,
    ErrorLoggingMixin, safe_execute, get_user_friendly_error
)


def test_error_handler():
    """에러 핸들러 기본 기능 테스트"""
    print("=== 에러 핸들러 테스트 ===")
    
    try:
        error_handler = ErrorHandler()
        
        # AWS 에러 처리 테스트
        from botocore.exceptions import ClientError
        
        # Mock AWS ClientError
        mock_error = Mock(spec=ClientError)
        mock_error.response = {
            'Error': {
                'Code': 'Throttling',
                'Message': 'Rate exceeded'
            }
        }
        
        standard_error = error_handler.handle_aws_error(mock_error)
        
        assert standard_error.error_code == "AWS_THROTTLING_ERROR"
        assert standard_error.category == ErrorCategory.AWS_SERVICE
        assert standard_error.severity == ErrorSeverity.WARNING
        
        print("✅ AWS 에러 처리 테스트 통과")
        
        # 설정 에러 처리 테스트
        config_error = ValueError("Invalid configuration value")
        standard_error = error_handler.handle_config_error(config_error)
        
        assert standard_error.error_code == "CONFIG_INVALID_ERROR"
        assert standard_error.category == ErrorCategory.CONFIGURATION
        
        print("✅ 설정 에러 처리 테스트 통과")
        
        # 사용자 친화적 메시지 테스트
        ko_message = error_handler.get_user_message("AWS_THROTTLING_ERROR", "ko")
        en_message = error_handler.get_user_message("AWS_THROTTLING_ERROR", "en")
        
        assert "요청이 너무 많아" in ko_message
        assert "Too many requests" in en_message
        
        print("✅ 다국어 메시지 테스트 통과")
        
        return True
        
    except Exception as e:
        print(f"❌ 에러 핸들러 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_standard_logger():
    """표준 로거 기본 기능 테스트"""
    print("\n=== 표준 로거 테스트 ===")
    
    try:
        # 임시 디렉토리에서 테스트
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = StandardLogger(
                name="test_logger",
                log_dir=temp_dir,
                enable_console=False  # 테스트 시 콘솔 출력 비활성화
            )
            
            # 기본 로깅 테스트
            logger.info("테스트 정보 메시지")
            logger.warning("테스트 경고 메시지")
            logger.error("테스트 에러 메시지")
            
            # 컨텍스트 설정 테스트
            logger.set_context(user_id="test_user", session_id="test_session")
            logger.info("컨텍스트가 포함된 메시지")
            
            # 성능 로깅 테스트
            logger.log_performance("test_operation", 1.5, True, test_param="value")
            
            # 모델 사용량 로깅 테스트
            tokens = {
                "input": 100,
                "output": 50,
                "total": 150
            }
            logger.log_model_usage("test-model", tokens)
            
            # 로그 파일 생성 확인
            log_files = list(Path(temp_dir).glob("*.log"))
            assert len(log_files) >= 3  # 메인, 성능, 사용량 로그
            
            print("✅ 기본 로깅 기능 테스트 통과")
            
            # 성능 타이머 컨텍스트 매니저 테스트
            with logger.performance_timer("context_test"):
                import time
                time.sleep(0.1)  # 0.1초 대기
            
            print("✅ 성능 타이머 테스트 통과")
            
            # 로그 통계 테스트
            stats = logger.get_log_stats()
            assert "log_directory" in stats
            assert "log_files" in stats
            
            print("✅ 로그 통계 테스트 통과")
            
        return True
        
    except Exception as e:
        print(f"❌ 표준 로거 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_logging_integration():
    """에러 처리와 로깅 통합 테스트"""
    print("\n=== 에러 처리 및 로깅 통합 테스트 ===")
    
    try:
        # 표준 에러 로깅 테스트
        error_handler = get_error_handler()
        logger = get_logger()
        
        # 표준 에러 생성 및 로깅
        test_error = ValueError("테스트 에러")
        standard_error = error_handler.handle_validation_error(test_error)
        logger.log_error(standard_error)
        
        print("✅ 표준 에러 로깅 테스트 통과")
        
        # 데코레이터 테스트
        @handle_errors(category="validation", reraise=False, return_on_error="에러 발생")
        def test_function_with_error():
            raise ValueError("데코레이터 테스트 에러")
        
        result = test_function_with_error()
        assert result == "에러 발생"
        
        print("✅ 에러 처리 데코레이터 테스트 통과")
        
        # 성능 로깅 데코레이터 테스트
        @log_performance(operation_name="test_performance")
        def test_performance_function():
            import time
            time.sleep(0.05)  # 0.05초 대기
            return "완료"
        
        result = test_performance_function()
        assert result == "완료"
        
        print("✅ 성능 로깅 데코레이터 테스트 통과")
        
        # 컨텍스트 매니저 테스트
        try:
            with error_context("validation", "test_context"):
                raise ValueError("컨텍스트 테스트 에러")
        except ValueError:
            pass  # 예상된 에러
        
        print("✅ 에러 컨텍스트 매니저 테스트 통과")
        
        with performance_context("context_performance_test"):
            import time
            time.sleep(0.05)
        
        print("✅ 성능 컨텍스트 매니저 테스트 통과")
        
        return True
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_logging_mixin():
    """ErrorLoggingMixin 테스트"""
    print("\n=== ErrorLoggingMixin 테스트 ===")
    
    try:
        class TestClass(ErrorLoggingMixin):
            def __init__(self):
                super().__init__()
            
            def test_method(self):
                self.log_info("테스트 메소드 실행")
                
                try:
                    raise ValueError("테스트 에러")
                except Exception as e:
                    self.handle_error(e, "validation")
                
                return "완료"
        
        test_obj = TestClass()
        result = test_obj.test_method()
        assert result == "완료"
        
        print("✅ ErrorLoggingMixin 테스트 통과")
        
        return True
        
    except Exception as e:
        print(f"❌ ErrorLoggingMixin 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utility_functions():
    """유틸리티 함수 테스트"""
    print("\n=== 유틸리티 함수 테스트 ===")
    
    try:
        # safe_execute 테스트
        def error_function():
            raise ValueError("테스트 에러")
        
        result = safe_execute(error_function, default="기본값")
        assert result == "기본값"
        
        def success_function():
            return "성공"
        
        result = safe_execute(success_function)
        assert result == "성공"
        
        print("✅ safe_execute 테스트 통과")
        
        # get_user_friendly_error 테스트
        test_error = ValueError("테스트 에러")
        ko_message = get_user_friendly_error(test_error, "ko")
        en_message = get_user_friendly_error(test_error, "en")
        
        assert isinstance(ko_message, str)
        assert isinstance(en_message, str)
        
        print("✅ get_user_friendly_error 테스트 통과")
        
        return True
        
    except Exception as e:
        print(f"❌ 유틸리티 함수 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_based_setup():
    """설정 기반 로깅 시스템 초기화 테스트"""
    print("\n=== 설정 기반 초기화 테스트 ===")
    
    try:
        config = {
            "logging": {
                "name": "config_test_logger",
                "level": "DEBUG",
                "log_dir": "test_logs",
                "max_file_size": 1024 * 1024,  # 1MB
                "backup_count": 3,
                "enable_console": False,
                "enable_file": True,
                "enable_json": True
            }
        }
        
        logger = setup_logging_from_config(config)
        
        assert logger.name == "config_test_logger"
        assert logger.logger.level == 10  # DEBUG level
        
        logger.info("설정 기반 로거 테스트")
        
        print("✅ 설정 기반 초기화 테스트 통과")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 기반 초기화 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """통합 테스트 실행"""
    print("🚀 에러 처리 및 로깅 시스템 통합 테스트 시작\n")
    
    tests = [
        test_error_handler,
        test_standard_logger,
        test_error_logging_integration,
        test_error_logging_mixin,
        test_utility_functions,
        test_config_based_setup
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 테스트 실행 중 예외 발생: {e}")
            failed += 1
    
    print(f"\n📊 테스트 결과:")
    print(f"✅ 통과: {passed}")
    print(f"❌ 실패: {failed}")
    print(f"📈 성공률: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 모든 테스트가 성공적으로 통과했습니다!")
        return True
    else:
        print(f"\n⚠️  {failed}개의 테스트가 실패했습니다.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)