# 코드 최적화 및 중복 제거 설계 문서

## 개요

Global Dual Nova RAG Chatbot 프로젝트의 코드 품질 향상과 유지보수성 개선을 위한 설계 문서입니다. 현재 코드베이스에서 발견된 중복 코드, 비효율적인 구현, 일관성 부족 문제를 해결하여 더 견고하고 확장 가능한 아키텍처를 구축합니다.

### 설계 목표
- **코드 중복 제거**: 게임 용어 단어장, 프롬프트 생성, AWS 클라이언트 초기화 등의 중복 제거
- **모듈화 개선**: 단일 파일에 집중된 로직을 기능별 모듈로 분리
- **표준화**: 명명 규칙, 에러 처리, 로깅 시스템 표준화
- **성능 최적화**: AWS 클라이언트 재사용, 효율적인 설정 관리
- **유지보수성 향상**: 명확한 인터페이스와 의존성 최소화

## 아키텍처

### 현재 아키텍처 문제점
1. **단일 파일 집중**: `src/chatbot_app.py`에 모든 로직이 집중 (1,000+ 라인)
2. **하드코딩된 데이터**: 게임 용어 단어장이 코드 내부에 하드코딩
3. **중복된 AWS 클라이언트**: 여러 곳에서 동일한 클라이언트 초기화
4. **일관성 부족**: Terraform 리소스 명명, 에러 처리 방식 불일치

### 개선된 아키텍처

```
src/
├── chatbot_app.py              # 메인 Streamlit 애플리케이션 (간소화)
├── core/                       # 핵심 비즈니스 로직
│   ├── __init__.py
│   ├── aws_clients.py          # AWS 클라이언트 관리 (싱글톤)
│   ├── prompt_generator.py     # 프롬프트 생성 통합 클래스
│   ├── streaming_handler.py    # 스트리밍 응답 처리 통합
│   └── dual_response.py        # 이중 언어 응답 생성
├── services/                   # 외부 서비스 연동
│   ├── __init__.py
│   ├── translation_service.py  # 번역 서비스
│   ├── knowledge_base.py       # Knowledge Base 검색
│   └── bedrock_service.py      # Bedrock 모델 호출
├── utils/                      # 유틸리티 함수
│   ├── __init__.py
│   ├── glossary_manager.py     # 게임 용어 단어장 관리
│   ├── config_manager.py       # 설정 관리
│   ├── logger.py               # 표준화된 로깅
│   └── error_handler.py        # 에러 처리 표준화
└── config/                     # 설정 파일
    ├── settings.py             # 애플리케이션 설정
    └── aws_config.py           # AWS 관련 설정
```

## 컴포넌트 및 인터페이스

### 1. AWS 클라이언트 관리 (aws_clients.py)

**설계 결정**: 싱글톤 패턴을 사용하여 AWS 클라이언트를 한 번만 초기화하고 재사용

```python
class AWSClientManager:
    """AWS 클라이언트 싱글톤 관리자"""
    _instance = None
    _clients = {}
    
    def get_client(self, service_name: str) -> boto3.client
    def initialize_clients(self) -> Dict[str, boto3.client]
    def health_check(self) -> Dict[str, bool]
```

**근거**: 현재 `@st.cache_resource`로 캐싱하고 있지만, 더 명시적이고 테스트 가능한 싱글톤 패턴 적용

### 2. 게임 용어 단어장 관리 (glossary_manager.py)

**설계 결정**: 외부 파일 기반 단어장 로딩과 fallback 메커니즘

```python
class GlossaryManager:
    """게임 용어 단어장 관리자"""
    
    def load_glossary(self) -> Dict[str, Any]
    def get_character_mapping(self) -> Dict[str, str]
    def get_term_translation(self, term: str, target_lang: str) -> str
    def validate_glossary(self, glossary: Dict) -> bool
```

**근거**: 현재 하드코딩된 단어장을 외부 JSON 파일로 분리하여 유지보수성 향상

### 3. 프롬프트 생성 통합 (prompt_generator.py)

**설계 결정**: 템플릿 패턴과 팩토리 패턴을 결합한 프롬프트 생성 시스템

```python
class BasePromptTemplate:
    """프롬프트 템플릿 기본 클래스"""
    def generate_prefix(self) -> str
    def generate_suffix(self, **kwargs) -> str
    def create_prompt(self, **kwargs) -> str

class TranslationPromptTemplate(BasePromptTemplate):
    """번역용 프롬프트 템플릿"""

class AnswerPromptTemplate(BasePromptTemplate):
    """답변 생성용 프롬프트 템플릿"""

class PromptFactory:
    """프롬프트 생성 팩토리"""
    def create_prompt(self, prompt_type: str, **kwargs) -> str
```

**근거**: 현재 중복된 프롬프트 생성 로직을 통합하고 새로운 언어 지원 시 확장 용이

### 4. 스트리밍 응답 처리 통합 (streaming_handler.py)

**설계 결정**: 언어별 중복 로직을 통합한 범용 스트리밍 핸들러

```python
class StreamingHandler:
    """범용 스트리밍 응답 처리기"""
    
    def stream_model_response(self, model_id: str, prompt: str, **kwargs) -> Iterator[str]
    def handle_parallel_streaming(self, tasks: List[StreamingTask]) -> Dict[str, str]
    def apply_typing_effect(self, text_stream: Iterator[str], delay: float = 0.02) -> None
```

**근거**: 한국어/영어 스트리밍 로직이 거의 동일하므로 통합하여 중복 제거

### 5. 설정 관리 시스템 (config_manager.py)

**설계 결정**: 계층적 설정 관리와 환경별 오버라이드 지원

```python
class ConfigManager:
    """중앙화된 설정 관리자"""
    
    def load_config(self, env: str = None) -> Dict[str, Any]
    def get_setting(self, key: str, default: Any = None) -> Any
    def validate_required_settings(self) -> List[str]  # 누락된 필수 설정 반환
    def reload_config(self) -> None
```

**근거**: 현재 분산된 환경 변수와 설정을 중앙화하여 관리 복잡성 감소

## 데이터 모델

### 설정 데이터 구조

```python
@dataclass
class AWSConfig:
    region: str
    bedrock_models: Dict[str, str]
    knowledge_base_id: str
    s3_bucket: str

@dataclass
class AppConfig:
    aws: AWSConfig
    ui_settings: Dict[str, Any]
    logging_level: str
    cache_settings: Dict[str, Any]

@dataclass
class GlossaryEntry:
    term: str
    translations: Dict[str, str]  # 언어별 번역
    aliases: List[str]
    category: str
    description: str
```

### 에러 처리 모델

```python
@dataclass
class StandardError:
    error_code: str
    message: str
    user_message: str  # 사용자 친화적 메시지
    context: Dict[str, Any]
    timestamp: datetime
    severity: str  # INFO, WARNING, ERROR, CRITICAL
```

## 에러 처리

### 표준화된 에러 처리 시스템

**설계 결정**: 일관된 에러 처리와 사용자 친화적 메시지 제공

```python
class ErrorHandler:
    """표준화된 에러 처리기"""
    
    def handle_aws_error(self, error: Exception) -> StandardError
    def handle_model_error(self, error: Exception) -> StandardError
    def log_error(self, error: StandardError) -> None
    def get_user_message(self, error_code: str, lang: str = "ko") -> str
```

### 에러 분류 및 처리 전략

1. **AWS 서비스 에러**: 재시도 로직과 fallback 메커니즘
2. **모델 호출 에러**: 대체 모델 사용 또는 캐시된 응답
3. **설정 에러**: 명확한 설정 가이드 제공
4. **네트워크 에러**: 자동 재시도와 타임아웃 처리

## 테스팅 전략

### 단위 테스트 구조

```
tests/
├── unit/
│   ├── test_aws_clients.py
│   ├── test_glossary_manager.py
│   ├── test_prompt_generator.py
│   └── test_config_manager.py
├── integration/
│   ├── test_bedrock_integration.py
│   └── test_knowledge_base.py
└── e2e/
    └── test_chatbot_flow.py
```

### 테스트 전략

1. **단위 테스트**: 각 모듈의 독립적 기능 검증
2. **통합 테스트**: AWS 서비스와의 연동 검증
3. **E2E 테스트**: 전체 챗봇 플로우 검증
4. **성능 테스트**: 응답 시간과 메모리 사용량 모니터링

## Terraform 리소스 표준화

### 명명 규칙 표준화

**설계 결정**: 일관된 리소스 명명과 태깅 시스템

```hcl
# 표준 명명 패턴: ${var.project_name}-${service}-${resource_type}-${environment}
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }
  
  resource_prefix = "${var.project_name}-${var.environment}"
}
```

### 리소스 모듈화

```
terraform/
├── modules/
│   ├── networking/     # VPC, 서브넷, 라우팅
│   ├── security/       # 보안 그룹, IAM 역할
│   ├── compute/        # ECS, ALB
│   └── storage/        # S3, Secrets Manager
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
└── main.tf            # 모듈 조합
```

## 성능 최적화

### 캐싱 전략

1. **프롬프트 캐싱**: Nova 모델의 prefix 캐싱 최적화
2. **설정 캐싱**: 자주 사용되는 설정값 메모리 캐싱
3. **단어장 캐싱**: 게임 용어 단어장 로딩 최적화
4. **AWS 클라이언트 재사용**: 연결 풀링과 세션 재사용

### 메모리 관리

1. **지연 로딩**: 필요한 시점에만 리소스 로딩
2. **가비지 컬렉션**: 대용량 응답 처리 후 메모리 정리
3. **스트리밍 최적화**: 버퍼 크기 조정과 백프레셔 처리

## 보안 고려사항

### 설정 보안

1. **Secrets Manager 통합**: 모든 민감한 설정을 Secrets Manager로 이관
2. **환경 변수 검증**: 필수 설정 누락 시 명확한 에러 메시지
3. **권한 최소화**: 각 컴포넌트별 최소 권한 원칙 적용

### 코드 보안

1. **입력 검증**: 사용자 입력에 대한 철저한 검증
2. **SQL 인젝션 방지**: 파라미터화된 쿼리 사용
3. **로그 보안**: 민감한 정보 로깅 방지

## 마이그레이션 전략

### 단계별 마이그레이션

1. **1단계**: 유틸리티 모듈 분리 (glossary_manager, config_manager)
2. **2단계**: AWS 클라이언트 통합 (aws_clients)
3. **3단계**: 프롬프트 생성 통합 (prompt_generator)
4. **4단계**: 스트리밍 핸들러 통합 (streaming_handler)
5. **5단계**: 메인 애플리케이션 리팩토링

### 호환성 유지

- 기존 API 인터페이스 유지
- 점진적 마이그레이션으로 서비스 중단 최소화
- 롤백 계획 수립
- 단계별로 테스트 주도 개발 방식으로 진행하여 기존 기능의 이슈 발생 가능성 최소화

## 모니터링 및 로깅

### 표준화된 로깅 시스템

```python
class StandardLogger:
    """표준화된 로깅 시스템"""
    
    def log_request(self, user_query: str, response_time: float) -> None
    def log_model_usage(self, model_id: str, tokens: Dict[str, int]) -> None
    def log_error(self, error: StandardError) -> None
    def log_performance(self, operation: str, duration: float) -> None
```

### 메트릭 수집

1. **응답 시간**: 각 모델별 응답 시간 추적
2. **토큰 사용량**: 비용 최적화를 위한 토큰 사용량 모니터링
3. **에러 발생률**: 서비스 안정성 모니터링
4. **사용자 패턴**: 질의 유형과 빈도 분석

이 설계는 현재 코드베이스의 문제점을 해결하면서도 기존 기능을 유지하고, 향후 확장성을 고려한 견고한 아키텍처를 제공합니다.