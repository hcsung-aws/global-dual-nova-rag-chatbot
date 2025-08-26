"""
에러 처리 및 로깅 시스템 사용 예시

이 파일은 새로운 표준화된 에러 처리 및 로깅 시스템을 
기존 코드에서 어떻게 사용하는지 보여주는 예시입니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import (
    get_logger, get_error_handler, handle_errors, log_performance,
    error_context, performance_context, log_aws_api_call, log_model_usage,
    ErrorLoggingMixin, safe_execute, get_user_friendly_error
)


# 예시 1: 기존 함수를 데코레이터로 개선
@handle_errors(category="aws", reraise=True)
@log_performance(operation_name="aws_bedrock_call")
@log_aws_api_call("bedrock", "invoke_model")
def invoke_bedrock_model(model_id: str, prompt: str):
    """
    기존의 Bedrock 모델 호출 함수를 개선한 예시
    
    기존 코드:
    try:
        response = client.invoke_model(...)
        return response
    except Exception as e:
        print(f"에러: {e}")
        return None
    
    개선된 코드: 데코레이터만 추가하면 자동으로 에러 처리 및 로깅
    """
    # 실제 Bedrock 호출 로직 (시뮬레이션)
    import time
    import random
    
    time.sleep(0.1)  # API 호출 시뮬레이션
    
    if random.random() < 0.1:  # 10% 확률로 에러 발생
        raise Exception("Bedrock API 호출 실패")
    
    return {
        "output": {"message": {"content": [{"text": f"응답: {prompt}"}]}},
        "usage": {
            "inputTokens": 100,
            "outputTokens": 50,
            "totalTokens": 150
        }
    }


# 예시 2: 컨텍스트 매니저 사용
def translate_text_improved(text: str, target_language: str):
    """
    기존의 번역 함수를 개선한 예시
    
    기존 코드:
    try:
        response = bedrock.invoke_model(...)
        return response
    except Exception as e:
        print(f"번역 오류: {e}")
        return text
    
    개선된 코드: 컨텍스트 매니저 사용
    """
    logger = get_logger()
    
    try:
        with error_context("model", "translation", model_id="nova-pro", text_length=len(text)):
            with performance_context("translation", target_language=target_language):
                # 번역 로직 시뮬레이션
                import time
                time.sleep(0.2)
                
                logger.info(f"번역 시작: {text[:50]}... -> {target_language}")
                
                # 실제 번역 API 호출
                result = invoke_bedrock_model("amazon.nova-pro-v1:0", f"Translate: {text}")
                
                logger.info("번역 완료")
                return result
                
    except Exception as e:
        # 에러가 발생해도 원본 텍스트 반환 (graceful degradation)
        user_message = get_user_friendly_error(e, "ko")
        logger.warning(f"번역 실패, 원본 반환: {user_message}")
        return {"translated_text": text}


# 예시 3: ErrorLoggingMixin을 사용한 클래스
class ImprovedAWSClientManager(ErrorLoggingMixin):
    """
    기존 AWSClientManager를 개선한 예시
    
    ErrorLoggingMixin을 상속받으면 자동으로 에러 처리 및 로깅 기능 제공
    """
    
    def __init__(self):
        super().__init__()
        self.clients = {}
        self.log_info("AWSClientManager 초기화")
    
    def get_client(self, service_name: str):
        """
        기존 코드:
        try:
            client = boto3.client(service_name)
            return client
        except Exception as e:
            print(f"클라이언트 생성 실패: {e}")
            return None
        
        개선된 코드: 믹스인의 메소드 사용
        """
        try:
            if service_name not in self.clients:
                self.log_info(f"새 클라이언트 생성: {service_name}")
                
                # 실제 클라이언트 생성 로직 (시뮬레이션)
                import time
                time.sleep(0.05)
                
                self.clients[service_name] = f"mock_{service_name}_client"
                self.log_performance(f"create_client_{service_name}", 0.05, True)
            
            return self.clients[service_name]
            
        except Exception as e:
            # 믹스인의 handle_error 메소드 사용
            standard_error = self.handle_error(e, "aws", {"service": service_name})
            return None
    
    def health_check(self):
        """헬스체크 메소드"""
        try:
            self.log_info("AWS 클라이언트 헬스체크 시작")
            
            # 각 클라이언트 상태 확인
            results = {}
            for service, client in self.clients.items():
                try:
                    # 헬스체크 로직 (시뮬레이션)
                    results[service] = "healthy"
                    self.log_info(f"{service} 클라이언트 정상")
                except Exception as e:
                    self.handle_error(e, "aws", {"service": service, "operation": "health_check"})
                    results[service] = "unhealthy"
            
            return results
            
        except Exception as e:
            self.handle_error(e, "aws", {"operation": "health_check"})
            return {}


# 예시 4: safe_execute 사용
def robust_knowledge_base_search(query: str):
    """
    기존의 Knowledge Base 검색을 안전하게 실행하는 예시
    
    기존 코드:
    try:
        results = bedrock_agent.retrieve(...)
        return results
    except Exception as e:
        print(f"검색 실패: {e}")
        return []
    
    개선된 코드: safe_execute 사용
    """
    def search_function():
        # 검색 로직 시뮬레이션
        import time
        import random
        
        time.sleep(0.3)
        
        if random.random() < 0.2:  # 20% 확률로 에러
            raise Exception("Knowledge Base 연결 실패")
        
        return [
            {"title": "문서1", "content": "내용1", "score": 0.9},
            {"title": "문서2", "content": "내용2", "score": 0.8}
        ]
    
    # safe_execute로 안전하게 실행
    results = safe_execute(
        search_function,
        default=[],  # 에러 시 빈 리스트 반환
        category="aws"
    )
    
    logger = get_logger()
    logger.info(f"Knowledge Base 검색 완료: {len(results)}개 결과")
    
    return results


# 예시 5: 모델 사용량 자동 로깅
@log_model_usage("amazon.nova-micro-v1:0")
def call_nova_micro(prompt: str):
    """
    Nova Micro 모델 호출 시 자동으로 토큰 사용량 로깅
    """
    # 모델 호출 시뮬레이션
    import time
    time.sleep(0.1)
    
    return {
        "output": {"message": {"content": [{"text": "응답"}]}},
        "usage": {
            "inputTokens": 50,
            "outputTokens": 25,
            "totalTokens": 75,
            "cacheReadInputTokenCount": 30,
            "cacheWriteInputTokenCount": 0
        }
    }


def demonstrate_usage():
    """사용 예시 데모"""
    print("🚀 에러 처리 및 로깅 시스템 사용 예시\n")
    
    # 로거 설정
    logger = get_logger()
    logger.set_context(user_id="demo_user", session_id="demo_session")
    
    print("1. Bedrock 모델 호출 (데코레이터 사용)")
    try:
        result = invoke_bedrock_model("amazon.nova-pro-v1:0", "안녕하세요")
        print(f"   결과: {result['output']['message']['content'][0]['text']}")
    except Exception as e:
        print(f"   에러: {get_user_friendly_error(e)}")
    
    print("\n2. 번역 함수 (컨텍스트 매니저 사용)")
    result = translate_text_improved("Hello, world!", "Korean")
    print(f"   번역 결과: {result}")
    
    print("\n3. AWS 클라이언트 관리 (ErrorLoggingMixin 사용)")
    manager = ImprovedAWSClientManager()
    client = manager.get_client("bedrock-runtime")
    health = manager.health_check()
    print(f"   클라이언트: {client}")
    print(f"   헬스체크: {health}")
    
    print("\n4. Knowledge Base 검색 (safe_execute 사용)")
    results = robust_knowledge_base_search("게임 캐릭터")
    print(f"   검색 결과: {len(results)}개")
    
    print("\n5. Nova Micro 호출 (자동 토큰 로깅)")
    result = call_nova_micro("간단한 질문")
    print(f"   응답: {result['output']['message']['content'][0]['text']}")
    
    print("\n✅ 모든 예시 실행 완료!")
    
    # 로그 통계 출력
    stats = logger.get_log_stats()
    print(f"\n📊 로그 통계:")
    print(f"   로그 디렉토리: {stats['log_directory']}")
    print(f"   로그 파일 수: {len(stats['log_files'])}")


if __name__ == "__main__":
    demonstrate_usage()