# Global Dual Nova RAG Chatbot - Terraform Infrastructure

이 디렉토리는 Global Dual Nova RAG Chatbot의 AWS 인프라를 관리하는 Terraform 코드를 포함합니다.

## 🏗️ 아키텍처 개요

### 모듈화된 구조
프로젝트는 다음과 같은 모듈로 구성되어 있습니다:

- **networking**: VPC, 서브넷, 라우팅 테이블, NAT 게이트웨이
- **security**: Security Groups, IAM 역할 및 정책
- **compute**: ECS 클러스터, ALB, Auto Scaling
- **storage**: S3 버킷, Secrets Manager

### 환경별 배포
- **dev**: 개발 환경 (비용 최적화, 최소 리소스)
- **prod**: 프로덕션 환경 (고가용성, 보안 강화)

## 📁 디렉토리 구조

```
terraform/
├── modules/                    # 재사용 가능한 모듈
│   ├── networking/            # VPC, 서브넷, 라우팅
│   ├── security/              # Security Groups, IAM
│   ├── compute/               # ECS, ALB, Auto Scaling
│   └── storage/               # S3, Secrets Manager
├── environments/              # 환경별 설정
│   ├── dev/                   # 개발 환경
│   └── prod/                  # 프로덕션 환경
├── main.tf                    # 기존 단일 파일 (레거시)
├── main-modular.tf           # 새로운 모듈화된 구조
├── variables.tf              # 변수 정의
├── outputs.tf                # 기존 출력 (레거시)
├── outputs-modular.tf        # 새로운 모듈화된 출력
└── README.md                 # 이 파일
```

## 🚀 사용법

### 1. 환경별 배포 (권장)

#### 개발 환경 배포
```bash
cd terraform/environments/dev
terraform init
terraform plan -var="knowledge_base_id=YOUR_KB_ID"
terraform apply -var="knowledge_base_id=YOUR_KB_ID"
```

#### 프로덕션 환경 배포
```bash
cd terraform/environments/prod
terraform init
terraform plan \
  -var="knowledge_base_id=YOUR_KB_ID" \
  -var="notion_token=YOUR_NOTION_TOKEN" \
  -var="ssl_certificate_arn=YOUR_SSL_CERT_ARN"
terraform apply \
  -var="knowledge_base_id=YOUR_KB_ID" \
  -var="notion_token=YOUR_NOTION_TOKEN" \
  -var="ssl_certificate_arn=YOUR_SSL_CERT_ARN"
```

### 2. 루트 디렉토리에서 모듈화된 배포

```bash
cd terraform
terraform init
terraform plan -var-file="environments/dev/terraform.tfvars"
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### 3. 기존 방식 (레거시)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## 🏷️ 표준화된 명명 규칙

### 리소스 명명 패턴
```
${project_name}-${environment}-${service}-${resource_type}
```

예시:
- `global-dual-nova-chatbot-prod-vpc`
- `global-dual-nova-chatbot-dev-ecs-cluster`
- `global-dual-nova-chatbot-prod-alb-sg`

### 태그 표준화
모든 리소스에 다음 태그가 자동으로 적용됩니다:

```hcl
{
  Project      = "global-dual-nova-chatbot"
  Environment  = "dev|prod"
  ManagedBy    = "Terraform"
  Owner        = "DevOps-Team"
  CostCenter   = "Engineering-Dev|Engineering-Prod"
  CreatedDate  = "YYYY-MM-DD"
  Application  = "global-dual-nova-rag-chatbot"
}
```

## 🔧 환경별 설정 차이점

### 개발 환경 (dev)
- **리소스**: 최소한의 CPU/메모리 (256 CPU, 512MB RAM)
- **Auto Scaling**: 비활성화
- **HTTPS**: 비활성화 (HTTP만 사용)
- **로그 보존**: 3일
- **인스턴스 수**: 1개 (고정)

### 프로덕션 환경 (prod)
- **리소스**: 충분한 CPU/메모리 (1024 CPU, 2048MB RAM)
- **Auto Scaling**: 활성화 (2-10 인스턴스)
- **HTTPS**: 필수 (SSL 인증서 필요)
- **로그 보존**: 30일
- **고가용성**: Multi-AZ 배포

## 📋 필수 변수

### 공통 필수 변수
- `knowledge_base_id`: Amazon Bedrock Knowledge Base ID

### 프로덕션 환경 추가 필수 변수
- `notion_token`: Notion API 토큰
- `ssl_certificate_arn`: SSL 인증서 ARN (HTTPS 사용 시)

## 🔍 모니터링 및 로깅

### CloudWatch 로그
- 로그 그룹: `/ecs/${project_name}-${environment}`
- Container Insights: 활성화
- ALB 액세스 로그: S3에 저장

### 태그 기반 비용 추적
- 환경별 비용 분석 가능
- 프로젝트별 리소스 그룹화
- Cost Center별 청구 분리

## 🛡️ 보안 고려사항

### 네트워크 보안
- ECS 태스크는 Private 서브넷에 배포
- ALB만 Public 서브넷에 위치
- Security Group으로 트래픽 제어

### 데이터 보안
- Secrets Manager로 민감한 정보 관리
- S3 버킷 암호화 활성화
- IAM 역할 최소 권한 원칙 적용

## 🔄 마이그레이션 가이드

### 기존 인프라에서 모듈화된 구조로 이전

1. **백업 생성**
   ```bash
   terraform state pull > backup.tfstate
   ```

2. **새로운 구조로 배포**
   ```bash
   cd environments/prod  # 또는 dev
   terraform init
   terraform import [기존 리소스들]
   ```

3. **검증 및 정리**
   ```bash
   terraform plan  # 변경사항 확인
   terraform apply  # 적용
   ```

## 📞 지원 및 문의

- **DevOps 팀**: devops@company.com
- **프로젝트 문서**: [링크]
- **이슈 트래킹**: [GitHub Issues]

## 📝 변경 이력

- **v2.0.0**: 모듈화된 구조 도입, 환경별 배포 지원
- **v1.0.0**: 초기 단일 파일 구조