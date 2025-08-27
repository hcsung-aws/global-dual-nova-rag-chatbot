# 릴리즈 노트 / Release Notes

> 📖 **English Version**: [RELEASE_NOTES_EN.md](RELEASE_NOTES_EN.md)

## 버전 0.1.0 (2025-08-28) - 첫 공개 버전

🎉 **Global Dual Nova RAG Chatbot의 첫 번째 공개 버전입니다!**

### 📋 주요 기능

- **이중 언어 지원**: 한국어(담당자용) + 영어(고객용) 응답
- **듀얼 모델 아키텍처**: Nova Micro(빠른 응답) + Nova Pro(상세 분석) 병렬 처리
- **RAG 통합**: Amazon Bedrock Knowledge Base를 활용한 맥락적 응답
- **실시간 스트리밍**: GitHub 원본 병렬 실행 패턴 적용
- **게임 캐릭터 인식**: 내장된 게임 용어집을 통한 캐릭터 식별

### 🗓️ 개발 히스토리

#### 2025-08-28
- **📁 프로젝트 구조 문서 업데이트**
  - 리팩토링 후 실제 프로젝트 구조를 반영하여 README 파일들 업데이트
  - src/ 디렉토리의 모듈화된 구조 반영 (config/, core/, services/, utils/)
  - terraform/ 구조에 modules/와 environments/ 서브디렉토리 추가
  - tests/, examples/, worklog/ 디렉토리 추가

#### 2025-08-27
- **🧪 테스트 코드 개선**
  - 현재 코드 구조에 맞게 테스트 호환성 개선
  - 성능 벤치마크 및 스트리밍 핸들러 테스트 수정

- **🔧 CloudWatch 오류 해결**
  - CloudWatch 로깅 오류 해결 및 애플리케이션 안정성 향상
  - 에러 핸들링 및 로깅 시스템 개선

- **🚀 AWS ECS Fargate 배포 완료**
  - 프로덕션 환경 배포 완료 및 문제 해결
  - 인프라 안정성 확보

- **⚡ 전체 시스템 리팩토링**
  - 코드 구조 최적화 및 모듈화
  - 성능 향상 및 유지보수성 개선

#### 2025-08-26
- **🛡️ 보안 및 접근 제어 기능 추가**
  - 포괄적인 보안 설정 및 접근 제어 기능 구현
  - AWS Secrets Manager 통합

#### 2025-08-25
- **📊 비용 분석 보고서 추가**
  - 상세한 비용 분석 및 모델 비교 보고서 작성
  - README에 비용 분석 섹션 추가

#### 2025-08-24
- **📝 문서화 개선**
  - 한글을 기본 README로 설정하고 영어 버전 분리
  - 프로젝트 문서 구조 개선

- **🚀 초기 릴리즈**
  - Global Dual Nova RAG Chatbot 첫 번째 버전 출시
  - 기본 기능 구현 완료

### 🏗️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python 3.9+
- **AI Models**: Amazon Bedrock Nova (Micro + Pro)
- **Infrastructure**: AWS ECS Fargate, Application Load Balancer
- **Storage**: Amazon S3, AWS Secrets Manager
- **Knowledge Base**: Amazon Bedrock Knowledge Bases
- **IaC**: Terraform

### 📈 성능 메트릭

- **응답 시간**: Micro 모델 1-3초, Pro 모델 3-8초
- **병렬 처리**: 총 ~3-5초
- **동시 사용자**: 100+ (자동 확장)
- **가용성**: 99.9% (다중 AZ 배포)

### 💰 비용 효율성

- **Nova Micro + Pro**: $46.34/월 (중간 복잡도 시나리오)
- **Claude 3.5 Sonnet 대비**: 77% 비용 절감
- **프롬프트 캐싱**: 추가 20-40% 절감 가능

### 🔒 보안 기능

- AWS Secrets Manager를 통한 민감 정보 관리
- VPC 프라이빗 서브넷 구성
- IAM 최소 권한 원칙 적용
- HTTPS/SSL 암호화
- 접근 제어 및 IP 제한 기능

### 🚀 배포 방법

```bash
git clone https://github.com/hcsung-aws/global-dual-nova-rag-chatbot.git
cd global-dual-nova-rag-chatbot
cd terraform
terraform init
terraform apply
```

### 🤝 기여자

- **Hyunchang Sung** (@hcsung-aws) - 프로젝트 리드 및 전체 개발

### 📄 라이선스

MIT License

---

**다음 버전 (0.2.0)에서 만나요! 🚀**
