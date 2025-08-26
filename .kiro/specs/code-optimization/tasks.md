# 코드 최적화 및 중복 제거 구현 계획

- [x] 1. 유틸리티 모듈 기반 구조 설정




  - 프로젝트 모듈 구조 생성 (src/core/, src/services/, src/utils/ 디렉토리)
  - 각 모듈에 __init__.py 파일 생성하여 Python 패키지로 설정
  - _요구사항: 8.1, 8.3_

- [x] 2. 게임 용어 단어장 관리 시스템 구현





  - [x] 2.1 GlossaryManager 클래스 구현


    - config/game_glossary.json 파일 로딩 기능 구현
    - 하드코딩된 단어장을 fallback으로 사용하는 로직 구현
    - 단어장 검증 및 에러 처리 기능 구현
    - _요구사항: 1.1, 1.2, 1.3_

  - [x] 2.2 기존 하드코딩된 단어장을 GlossaryManager로 교체


    - get_game_glossary() 함수를 GlossaryManager 사용으로 변경
    - 모든 단어장 참조를 중앙화된 관리자로 통합
    - _요구사항: 1.1, 1.2_

- [x] 3. AWS 클라이언트 관리 시스템 구현





  - [x] 3.1 AWSClientManager 싱글톤 클래스 구현


    - 싱글톤 패턴으로 AWS 클라이언트 관리 클래스 생성
    - 클라이언트 초기화, 재사용, 헬스체크 기능 구현
    - 에러 처리 및 재시도 로직 구현
    - _요구사항: 3.1, 3.2, 3.3_

  - [x] 3.2 기존 AWS 클라이언트 초기화를 AWSClientManager로 교체


    - @st.cache_resource get_aws_clients() 함수를 AWSClientManager로 변경
    - 모든 AWS 서비스 호출을 통합된 클라이언트 관리자로 변경
    - _요구사항: 3.1, 3.2_

- [x] 4. 설정 관리 시스템 구현





  - [x] 4.1 ConfigManager 클래스 구현


    - 중앙화된 설정 관리 클래스 생성
    - 환경별 설정 오버라이드 지원 구현
    - 필수 설정 검증 및 에러 메시지 제공 기능 구현
    - _요구사항: 6.1, 6.2, 6.3_

  - [x] 4.2 설정 데이터 모델 구현


    - AWSConfig, AppConfig 데이터클래스 생성
    - 설정 검증 로직 구현
    - _요구사항: 6.1, 6.2_

- [x] 5. 에러 처리 및 로깅 표준화 구현




  - [x] 5.1 표준화된 에러 처리 시스템 구현


    - StandardError 데이터클래스 및 ErrorHandler 클래스 구현
    - AWS, 모델, 설정 에러별 처리 로직 구현
    - 사용자 친화적 에러 메시지 시스템 구현
    - _요구사항: 7.1, 7.2, 7.3_

  - [x] 5.2 표준화된 로깅 시스템 구현


    - StandardLogger 클래스 구현
    - 일관된 로그 형식 및 레벨 관리 구현
    - 성능 및 사용량 로깅 기능 구현
    - _요구사항: 7.1, 7.3_

- [x] 6. 프롬프트 생성 시스템 통합





  - [x] 6.1 프롬프트 템플릿 시스템 구현


    - BasePromptTemplate, TranslationPromptTemplate, AnswerPromptTemplate 클래스 구현
    - 템플릿 패턴을 사용한 프롬프트 생성 로직 구현
    - _요구사항: 2.1, 2.2, 2.3_

  - [x] 6.2 PromptFactory 클래스 구현

    - 프롬프트 타입별 생성 팩토리 구현
    - 기존 create_translation_prompt_prefix(), create_answer_prompt_prefix() 함수를 통합
    - _요구사항: 2.1, 2.2_

  - [x] 6.3 기존 프롬프트 생성 로직을 통합 시스템으로 교체


    - 모든 프롬프트 생성을 PromptFactory를 통해 처리하도록 변경
    - 중복된 프롬프트 생성 코드 제거
    - _요구사항: 2.1, 2.2_

- [ ] 7. 스트리밍 응답 처리 통합





  - [x] 7.1 StreamingHandler 클래스 구현



    - 범용 스트리밍 응답 처리 클래스 구현
    - 병렬 스트리밍 처리 및 타이핑 효과 기능 구현
    - _요구사항: 4.1, 4.2, 4.3_

  - [x] 7.2 기존 스트리밍 로직을 StreamingHandler로 통합




    - stream_nova_model() 함수를 StreamingHandler로 통합
    - 한국어/영어 중복 스트리밍 로직 제거
    - _요구사항: 4.1, 4.2_

- [x] 8. 서비스 레이어 구현




  - [x] 8.1 번역 서비스 모듈 분리


    - TranslationService 클래스 구현
    - translate_text_with_caching() 함수를 서비스 클래스로 이동
    - _요구사항: 8.1, 8.2, 8.4_

  - [x] 8.2 Knowledge Base 서비스 모듈 분리


    - KnowledgeBaseService 클래스 구현
    - search_knowledge_base() 함수를 서비스 클래스로 이동
    - _요구사항: 8.1, 8.2, 8.4_

  - [x] 8.3 Bedrock 서비스 모듈 분리


    - BedrockService 클래스 구현
    - Nova 모델 호출 로직을 서비스 클래스로 이동
    - _요구사항: 8.1, 8.2, 8.4_
-

- [x] 9. 메인 애플리케이션 리팩토링




  - [x] 9.1 메인 애플리케이션에서 비즈니스 로직 분리


    - generate_dual_answer(), generate_dual_language_response() 함수를 core 모듈로 이동
    - UI 로직과 비즈니스 로직 분리
    - _요구사항: 8.1, 8.2, 8.4_

  - [x] 9.2 의존성 주입 및 모듈 통합



    - 모든 새로운 모듈들을 메인 애플리케이션에 통합
    - 기존 함수들을 새로운 클래스 기반 구조로 교체
    - _요구사항: 8.3, 8.4_

- [x] 10. 단위 테스트 구현



  - [x] 10.1 핵심 모듈 단위 테스트 작성


    - GlossaryManager, AWSClientManager, ConfigManager 테스트 작성
    - 각 모듈의 독립적 기능 검증 테스트 구현
    - _요구사항: 모든 요구사항의 검증_

  - [x] 10.2 서비스 레이어 단위 테스트 작성


    - TranslationService, KnowledgeBaseService, BedrockService 테스트 작성
    - 모킹을 사용한 외부 의존성 테스트 구현
    - _요구사항: 모든 요구사항의 검증_

- [x] 11. Terraform 리소스 표준화




  - [x] 11.1 명명 규칙 표준화 적용


    - 모든 Terraform 리소스에 일관된 명명 패턴 적용
    - 표준화된 태그 세트 구현
    - _요구사항: 5.1, 5.2, 5.3_


  - [x] 11.2 리소스 모듈화 구현

    - Terraform 코드를 기능별 모듈로 분리
    - 환경별 설정 관리 구조 구현
    - _요구사항: 5.1, 5.2_

- [x] 12. 통합 테스트 및 검증






  - [x] 12.1 전체 시스템 통합 테스트


    - 리팩토링된 시스템의 전체 플로우 테스트
    - 기존 기능 동작 검증 및 성능 테스트
    - _요구사항: 모든 요구사항의 최종 검증_

  - [x] 12.2 마이그레이션 검증 및 문서화


    - 기존 기능과의 호환성 검증
    - 성능 개선 및 코드 품질 향상 측정
    - _요구사항: 모든 요구사항의 최종 검증_