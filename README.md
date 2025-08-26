# Global Dual Nova RAG Chatbot

🌍 **Amazon Bedrock Nova 모델을 활용한 엔터프라이즈급 다국어 고객 서비스 챗봇**으로, 이중 언어 지원과 RAG(Retrieval-Augmented Generation) 기능을 제공합니다.

> 📖 **English Version**: [README_EN.md](README_EN.md)

## 🚀 주요 기능

### 핵심 기능
- **이중 언어 지원**: 한국어(담당자용) + 영어(고객용) 응답
- **듀얼 모델 아키텍처**: Nova Micro(빠른 응답) + Nova Pro(상세 분석) 병렬 처리
- **RAG 통합**: Amazon Bedrock Knowledge Base를 활용한 맥락적 응답
- **실시간 스트리밍**: GitHub 원본 병렬 실행 패턴 적용
- **게임 캐릭터 인식**: 내장된 게임 용어집을 통한 캐릭터 식별

### 기술적 특징
- **진정한 병렬 처리**: ThreadPoolExecutor 기반 동시 모델 실행
- **버퍼 기반 스트리밍**: 자연스러운 타이핑 효과를 통한 실시간 응답 표시
- **프롬프트 캐싱**: Nova 모델 캐싱을 통한 성능 향상
- **자동 확장 인프라**: AWS ECS Fargate와 Application Load Balancer
- **보안 설정**: AWS Secrets Manager 통합

## 📋 사전 요구사항

- 적절한 권한을 가진 AWS 계정
- Terraform >= 1.0
- AWS CLI 설정 완료
- Amazon Bedrock 액세스 활성화
- Amazon Bedrock에서 생성된 Knowledge Base

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │    │   Load Balancer  │    │   ECS Fargate   │
│   Load Balancer │◄──►│                  │◄──►│   Container     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐             │
                       │   Secrets        │◄────────────┘
                       │   Manager        │
                       └──────────────────┘
                                │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Amazon        │    │   Amazon         │    │   Amazon        │
│   Bedrock       │◄──►│   Bedrock        │◄──►│   S3 Bucket     │
│   Nova Models   │    │   Knowledge Base │    │   (Code Storage)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/hcsung-aws/global-dual-nova-rag-chatbot.git
cd global-dual-nova-rag-chatbot
```

### 2. AWS 자격 증명 설정
```bash
aws configure
```

### 3. Knowledge Base 생성
1. Amazon Bedrock 콘솔로 이동
2. 새 Knowledge Base 생성
3. Knowledge Base ID 기록
4. `terraform/variables.tf`에 Knowledge Base ID 업데이트

### 4. 인프라 배포
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 5. 애플리케이션 접속
배포 완료 후 Terraform이 Application Load Balancer URL을 출력합니다.

## 📁 프로젝트 구조

```
global-dual-nova-rag-chatbot/
├── src/
│   └── chatbot_app.py          # 메인 Streamlit 애플리케이션
├── terraform/
│   ├── main.tf                 # 메인 인프라 설정
│   ├── variables.tf            # 입력 변수
│   ├── outputs.tf              # 출력 값
│   ├── ecs.tf                  # ECS 서비스 설정
│   ├── alb.tf                  # Application Load Balancer
│   ├── secrets.tf              # Secrets Manager 설정
│   └── s3.tf                   # 코드 저장용 S3 버킷
├── config/
│   ├── requirements.txt        # Python 의존성
│   └── game_glossary.json      # 게임 캐릭터 용어집
├── docs/
│   ├── ARCHITECTURE.md         # 상세 아키텍처 문서
│   ├── DEPLOYMENT.md           # 배포 가이드
│   ├── API.md                  # API 문서
│   └── COST_ANALYSIS.md        # 비용 분석 보고서
├── assets/
│   └── architecture-diagram.txt # 아키텍처 다이어그램
├── scripts/
│   ├── deploy.sh               # 배포 스크립트
│   └── cleanup.sh              # 정리 스크립트
└── README.md                   # 이 파일
```

## 🔧 설정

### 환경 변수
애플리케이션은 AWS Secrets Manager를 사용하여 설정을 관리합니다:

- `NOTION_TOKEN_SECRET_ARN`: Notion API 토큰 (Notion 통합 사용 시)
- `APP_CONFIG_SECRET_ARN`: Knowledge Base ID를 포함한 애플리케이션 설정

### Knowledge Base 설정
시크릿에서 Knowledge Base ID를 업데이트하세요:
```json
{
  "knowledge_base_id": "your-knowledge-base-id-here",
  "data_source_ids": ["your-data-source-id-here"]
}
```

## 🎯 사용법

### 한국어 사용자
- 한국어로 질문
- GitHub 원본 병렬 처리(Micro + Pro)를 사용한 응답 수신

### 영어 사용자
- 영어로 질문
- 이중 언어 응답 수신:
  1. 한국어 응답 (담당자 확인용)
  2. 영어 응답 (고객용)

### 언어 감지
시스템이 자동으로 입력 언어를 감지하고 적절히 응답합니다.

## 🔄 듀얼 모델 처리

### GitHub 원본 패턴
```python
# Pro 모델을 백그라운드에서 실행
with ThreadPoolExecutor(max_workers=2) as executor:
    future_pro = executor.submit(collect_pro_stream)
    
    # Micro 모델을 실시간으로 스트리밍
    for chunk in stream_nova_model('nova-micro', prompt):
        display_chunk(chunk)
    
    # Pro 결과를 버퍼에서 표시
    display_pro_results(future_pro.result())
```

### 성능상 이점
- **빠른 응답 시간**: Micro 모델이 즉각적인 피드백 제공
- **상세한 분석**: Pro 모델이 포괄적인 인사이트 추가
- **병렬 실행**: 두 모델이 동시에 실행
- **자연스러운 흐름**: 버퍼 기반 스트리밍으로 부드러운 사용자 경험

## 📊 모니터링

### CloudWatch 메트릭
- ECS 서비스 상태
- Application Load Balancer 메트릭
- Bedrock API 사용량
- 응답 시간

### 로깅
- CloudWatch의 애플리케이션 로그
- ECS 태스크 로그
- 로드 밸런서 액세스 로그

## 💰 비용 분석

### 모델 비용 비교
현재 구현된 **Nova Micro + Pro 병렬 처리** 방식은 다른 모델 대비 뛰어난 비용 효율성을 제공합니다:

| 모델 구성 | 월간 비용* | 비용 차이 | 특징 |
|-----------|------------|-----------|------|
| **Nova Micro + Pro (현재)** | **$46.34** | 기준 | ⭐⭐⭐⭐⭐ 최적 균형 |
| Claude 3.5 Sonnet | $202.50 | **+337%** | 높은 품질, 높은 비용 |
| Claude 3.5 Haiku | $16.88 | **-64%** | 저비용, 제한된 기능 |

*중간 복잡도 시나리오 기준 (일일 500 요청)

### 핵심 비용 절감 요소
- **Claude 3.5 Sonnet 대비 77% 비용 절감**
- **프롬프트 캐싱으로 추가 20-40% 절감 가능**
- **병렬 처리로 사용자 경험 최적화**
- **이중 언어 지원의 독특한 가치**

📊 **상세 분석**: [COST_ANALYSIS.md](docs/COST_ANALYSIS.md)

## 🔒 보안

### 접근 제어 설정
기본적으로 **공개 접근**이 가능하도록 설정되어 있습니다. 프로덕션 환경에서는 **반드시 접근을 제한**하세요:

```hcl
# terraform.tfvars - 제한된 접근 (권장)
restrict_public_access = true
admin_ip_addresses     = [
  "203.0.113.1",    # 사무실 IP
  "198.51.100.1"    # 집 IP
]
```

🛡️ **보안 설정 가이드**: [SECURITY_CONFIGURATION.md](docs/SECURITY_CONFIGURATION.md)

### 구현된 모범 사례
- **시크릿 관리**: AWS Secrets Manager에 모든 민감한 데이터 저장
- **네트워크 보안**: 프라이빗 서브넷이 있는 VPC
- **IAM 역할**: 최소 권한 액세스
- **HTTPS**: SSL/TLS 암호화
- **컨테이너 보안**: Fargate 관리형 컨테이너

## 🚀 확장

### 자동 확장
- CPU/메모리 기반 ECS 서비스 자동 확장
- Application Load Balancer가 트래픽 분산
- Fargate가 인프라를 자동으로 관리

### 비용 최적화
- Fargate Spot 인스턴스 (선택사항)
- Bedrock 온디맨드 요금제
- S3 라이프사이클 정책

## 🛠️ 개발

### 로컬 개발
```bash
# 의존성 설치
pip install -r config/requirements.txt

# 환경 변수 설정
export AWS_DEFAULT_REGION=us-east-1
export DATA_BUCKET_NAME=your-bucket-name

# 로컬 실행
streamlit run src/chatbot_app.py
```

### 테스트
```bash
# Bedrock 연결 테스트
python scripts/test_bedrock.py

# Knowledge Base 테스트
python scripts/test_knowledge_base.py
```

## 📈 성능 메트릭

### 응답 시간 (일반적)
- **Micro 모델**: 1-3초
- **Pro 모델**: 3-8초
- **병렬 처리**: 총 ~3-5초
- **Knowledge Base 쿼리**: 0.5-2초

### 처리량
- **동시 사용자**: 100+ (자동 확장 포함)
- **초당 요청 수**: 컨테이너당 50+
- **가용성**: 99.9% (다중 AZ 배포)

## 🤝 기여

1. 저장소 포크
2. 기능 브랜치 생성
3. 변경사항 작성
4. 테스트 추가
5. 풀 리퀘스트 제출

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 라이선스가 부여됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🆘 지원

### 일반적인 문제
- **Bedrock 액세스**: 해당 리전에서 Bedrock이 활성화되어 있는지 확인
- **Knowledge Base**: Knowledge Base ID가 올바른지 확인
- **권한**: IAM 역할에 필요한 권한이 있는지 확인

### 도움 받기
- 이 저장소에서 이슈 생성
- 자세한 가이드는 [docs/](docs/) 디렉토리 확인
- 디버깅을 위해 CloudWatch 로그 검토

## 🏆 감사의 말

- [Hyunsoo0128/Dual_Model_ChatBot](https://github.com/Hyunsoo0128/Dual_Model_ChatBot)의 원본 듀얼 모델 패턴을 기반으로 함
- 게임 내 채팅 번역 및 단어장 기능은 [카카오게임즈의 Amazon Bedrock 활용 사례](https://aws.amazon.com/ko/blogs/tech/kakaogames-amazon-bedrock-in-game-chat-translation/)를 참고하여 구현
- Amazon Bedrock Nova 모델로 구동
- Streamlit 및 AWS 서비스로 구축

---

**글로벌 고객 서비스 우수성을 위해 ❤️로 제작되었습니다**
