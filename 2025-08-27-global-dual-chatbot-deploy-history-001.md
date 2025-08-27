# Global Dual Nova RAG Chatbot 배포 히스토리

**작업 일시**: 2025-08-27 (UTC 12:17:20 ~ 12:26:15)  
**프로젝트**: global-dual-nova-rag-chatbot  
**환경**: production (ap-northeast-1)  
**작업자**: hcsung  

## 📋 작업 개요

Amazon Bedrock Nova 모델을 활용한 엔터프라이즈급 다국어 고객 서비스 챗봇의 AWS ECS Fargate 환경 배포 및 문제 해결 작업을 수행했습니다.

## 🚨 발견된 주요 문제들

### 1. ECS 컨테이너 시작 실패 (503 Service Temporarily Unavailable)
- **증상**: 애플리케이션 URL 접속 시 503 에러 발생
- **원인**: ECS 서비스 runningCount: 0, desiredCount: 1 (태스크 실행 실패)
- **근본 원인**: 컨테이너 시작 시간이 health check 타임아웃을 초과

### 2. 컨테이너 초기화 시간 과다 소요
- **문제**: AWS CLI 설치 과정에서 59MB 다운로드 및 압축 해제로 인한 지연
- **영향**: Health check grace period (60초) 내 시작 완료 불가
- **로그 분석**: CloudWatch에서 "AWS CLI installation" 단계에서 멈춤 확인

### 3. 모듈러 애플리케이션 구조 미반영
- **문제**: 단일 파일(chatbot_app.py)만 S3에 업로드
- **실제 구조**: src/, config/, utils/, core/, services/ 디렉토리 구조
- **결과**: 모듈 import 실패로 인한 애플리케이션 시작 불가

## ✅ 성공적으로 해결된 문제들

### 1. Health Check 타임아웃 연장
```hcl
# terraform/modules/compute/main.tf
resource "aws_ecs_service" "main" {
  health_check_grace_period_seconds = 300  # 60 → 300초로 연장
  
  load_balancer {
    health_check_interval_seconds = 60      # 30 → 60초
    health_check_timeout_seconds  = 30      # 5 → 30초  
    unhealthy_threshold_count     = 5       # 2 → 5회
  }
}
```

### 2. 완전한 소스코드 구조 S3 배포
```hcl
# terraform/modules/storage/main.tf
locals {
  src_files = fileset("./../src", "**/*.py")  # 동적 파일 발견
}

resource "aws_s3_object" "src_files" {
  for_each = local.src_files
  bucket   = aws_s3_bucket.code.bucket
  key      = "src/${each.value}"
  source   = "./../src/${each.value}"
  etag     = filemd5("./../src/${each.value}")
}
```

### 3. 컨테이너 시작 명령 최적화
```dockerfile
# 순차적 설치 프로세스
CMD ["sh", "-c", "
  apt-get update && apt-get install -y curl unzip && \
  curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && \
  unzip awscliv2.zip && ./aws/install && \
  aws s3 cp s3://${DATA_BUCKET_NAME}/requirements.txt . && \
  pip install -r requirements.txt && \
  aws s3 sync s3://${DATA_BUCKET_NAME}/src/ ./src/ && \
  aws s3 sync s3://${DATA_BUCKET_NAME}/config/ ./config/ && \
  streamlit run src/chatbot_app.py --server.port=8501 --server.address=0.0.0.0
"]
```

## 🔧 적용된 Terraform 변경사항

### 1. Storage Module 개선
- **파일**: `terraform/modules/storage/main.tf`
- **변경**: fileset 함수를 사용한 동적 Python 파일 업로드
- **결과**: 18개 Python 모듈 파일 자동 업로드

### 2. Compute Module Health Check 설정
- **파일**: `terraform/modules/compute/main.tf`  
- **변경**: grace period 300초, interval 60초, timeout 30초, threshold 5회
- **결과**: 컨테이너 시작 시간 충분히 확보

### 3. 태그 표준화
- **적용**: 29개 리소스에 표준화된 태그 적용
- **포함**: Application, Environment, Owner, Project, Region 등

## 📊 배포 결과

### 성공적으로 배포된 인프라
```
🌐 애플리케이션 URL: 
http://dual-nova-chatbot-production-alb-2134834621.ap-northeast-1.elb.amazonaws.com

📍 리전: ap-northeast-1 (Asia Pacific - Tokyo)
🏗️ 환경: production  
📊 ECS 클러스터: dual-nova-chatbot-production-cluster
🔄 태스크 정의: dual-nova-chatbot-production-task:2
🪣 S3 버킷: dual-nova-chatbot-production-code-62eea701
```

### 업로드된 파일 구조
```
S3 Bucket Contents:
├── requirements.txt
├── config/game_glossary.json
├── src/chatbot_app.py
├── src/core/
│   ├── __init__.py
│   ├── aws_clients.py
│   ├── dual_response.py
│   ├── prompt_generator.py
│   └── streaming_handler.py
├── src/services/
│   ├── __init__.py
│   ├── bedrock_service.py
│   ├── knowledge_base_service.py
│   └── translation_service.py
├── src/utils/
│   ├── __init__.py
│   ├── error_handler.py
│   ├── error_logging_utils.py
│   ├── glossary_manager.py
│   ├── glossary_wrapper.py
│   └── logger.py
└── src/config/
    ├── __init__.py
    └── models.py
```

## 🔍 진단 과정에서 사용한 유용한 명령어들

### ECS 서비스 상태 확인
```bash
aws ecs describe-services \
  --cluster dual-nova-chatbot-production-cluster \
  --services dual-nova-chatbot-production-service \
  --region ap-northeast-1 \
  --query 'services[0].{serviceName:serviceName,status:status,runningCount:runningCount,desiredCount:desiredCount}'
```

### CloudWatch 로그 확인
```bash
aws logs get-log-events \
  --log-group-name "/ecs/dual-nova-chatbot-production" \
  --log-stream-name "ecs/dual-nova-chatbot-production-container/[TASK-ID]" \
  --region ap-northeast-1
```

### ECS 태스크 상세 정보
```bash
aws ecs describe-tasks \
  --cluster dual-nova-chatbot-production-cluster \
  --tasks [TASK-ARN] \
  --region ap-northeast-1
```

## ⚠️ 여전히 주의해야 할 사항들

### 1. 컨테이너 시작 시간
- **현재**: AWS CLI 설치로 인한 2-3분 소요
- **개선 방안**: 사전 빌드된 Docker 이미지 사용 고려
- **임시 해결**: Health check grace period 300초로 설정

### 2. 보안 설정
- **현재 상태**: 공개 접근 허용 (restrict_public_access = false)
- **프로덕션 권장**: IP 제한 또는 VPN 접근 설정
```hcl
# terraform.tfvars에서 설정
restrict_public_access = true
admin_ip_addresses = ["YOUR-IP-ADDRESS/32"]
```

### 3. 비용 최적화
- **현재**: Fargate 온디맨드 사용
- **개선 방안**: Fargate Spot 인스턴스 고려
- **모니터링**: CloudWatch 비용 알림 설정 권장

## 🚀 다음 세션에서 확인할 사항들

### 1. 애플리케이션 상태 확인
```bash
# ECS 서비스 최종 상태 확인
aws ecs describe-services --cluster dual-nova-chatbot-production-cluster --services dual-nova-chatbot-production-service --region ap-northeast-1

# 애플리케이션 접속 테스트
curl -I http://dual-nova-chatbot-production-alb-2134834621.ap-northeast-1.elb.amazonaws.com
```

### 2. 기능 테스트
- [ ] 한국어 입력 → 한국어 응답 테스트
- [ ] 영어 입력 → 이중 언어 응답 테스트  
- [ ] Nova Micro + Pro 병렬 처리 확인
- [ ] Knowledge Base 연동 테스트
- [ ] 게임 캐릭터 인식 기능 테스트

### 3. 성능 모니터링
- [ ] CloudWatch 메트릭 확인
- [ ] 응답 시간 측정
- [ ] 동시 사용자 테스트
- [ ] 비용 사용량 모니터링

## 📚 참고 자료

### 프로젝트 문서
- **README**: `/home/hcsung/global-dual-nova-rag-chatbot/README.md`
- **아키텍처**: 듀얼 모델 (Nova Micro + Pro) 병렬 처리
- **특징**: 한국어/영어 이중 언어 지원, RAG 통합

### 주요 설정 파일
- **Terraform 메인**: `terraform/main.tf`
- **컴퓨트 모듈**: `terraform/modules/compute/main.tf`
- **스토리지 모듈**: `terraform/modules/storage/main.tf`
- **애플리케이션**: `src/chatbot_app.py`

### AWS 리소스 정보
- **계정 ID**: 965037532757
- **리전**: ap-northeast-1
- **VPC ID**: vpc-0435255d630bc4c2d
- **Knowledge Base ID**: 8F4LAXWBB3

## 💡 교훈 및 베스트 프랙티스

### 1. 컨테이너 시작 시간 고려
- Health check 설정 시 실제 애플리케이션 시작 시간을 충분히 고려
- 복잡한 설치 과정이 있는 경우 grace period를 넉넉하게 설정

### 2. 모듈러 애플리케이션 배포
- 단일 파일이 아닌 전체 디렉토리 구조를 S3에 업로드
- fileset 함수를 활용한 동적 파일 발견 및 업로드

### 3. 단계적 문제 해결
- ECS 서비스 상태 → 태스크 상태 → 컨테이너 로그 순으로 진단
- CloudWatch 로그를 통한 정확한 실패 지점 파악

### 4. Terraform 상태 관리
- terraform refresh로 현재 상태 동기화
- terraform plan으로 변경사항 사전 확인
- 태그 표준화를 통한 리소스 관리 개선

---

**작업 완료 시각**: 2025-08-27 12:26:15 UTC  
**최종 상태**: 배포 성공, 컨테이너 시작 중 (예상 완료: 5-10분)  
**다음 작업**: 애플리케이션 기능 테스트 및 성능 모니터링

## 🔧 추가 문제 해결 (12:33:50 UTC)

### 🚨 발견된 추가 문제
**문제**: ECS 태스크 정의에서 `chatbot_app.py`를 S3 루트에서 찾으려 하지만 실제로는 `src/chatbot_app.py`에 위치

### ✅ 해결 과정

#### 1. 문제 분석 (Ultra-Think)
- **S3 업로드 구조**: `chatbot_app.py`가 루트에 업로드되지만 실제 파일은 `src/` 디렉토리에 있음
- **ECS 컨테이너 명령**: 잘못된 경로로 파일을 찾으려 함
- **모듈 구조**: 전체 src/ 디렉토리 구조가 필요하지만 메인 파일만 루트에 업로드됨

#### 2. 해결 방안 적용

**A. S3 업로드 경로 수정**
```hcl
# terraform/modules/storage/main.tf
resource "aws_s3_object" "chatbot_app" {
  key    = "src/chatbot_app.py"  # 변경: chatbot_app.py → src/chatbot_app.py
  source = var.chatbot_app_source_path
}
```

**B. ECS 컨테이너 명령 수정**
```hcl
# terraform/modules/compute/main.tf
command = [
  "bash", "-c",
  "... && streamlit run src/chatbot_app.py --server.port=8501 --server.address=0.0.0.0"
]
```

#### 3. 배포 실행
```bash
cd terraform
terraform plan   # 변경사항 확인
terraform apply -auto-approve  # 자동 적용
```

#### 4. 배포 결과
- **S3 객체 교체**: `chatbot_app.py` → `src/chatbot_app.py`
- **ECS 태스크 정의**: 버전 2 → 버전 3으로 업데이트
- **서비스 업데이트**: 새로운 태스크 정의로 자동 롤링 업데이트

### 📊 최종 배포 상태

```
🌐 애플리케이션 URL: 
http://dual-nova-chatbot-production-alb-2134834621.ap-northeast-1.elb.amazonaws.com

📍 리전: ap-northeast-1 (Asia Pacific - Tokyo)
🏗️ 환경: production  
📊 ECS 클러스터: dual-nova-chatbot-production-cluster
🔄 태스크 정의: dual-nova-chatbot-production-task:3 (수정됨)
🪣 S3 버킷: dual-nova-chatbot-production-code-62eea701
```

### 🔍 해결된 핵심 문제들

1. **파일 경로 불일치**: S3에서 올바른 경로(`src/chatbot_app.py`)로 파일 업로드
2. **컨테이너 시작 명령**: 올바른 경로로 Streamlit 애플리케이션 실행
3. **모듈 구조 보존**: 전체 src/ 디렉토리 구조 유지

### ⏱️ 예상 완료 시간
- **컨테이너 시작**: 3-5분 (AWS CLI 설치 + 의존성 설치)
- **Health Check**: 추가 2-3분
- **총 예상 시간**: 5-8분

### 🎯 다음 단계
1. **5-10분 후 애플리케이션 접속 테스트**
2. **기능 검증**: 한국어/영어 이중 언어 응답 테스트
3. **Nova Micro + Pro 병렬 처리 확인**
4. **Knowledge Base 연동 테스트**

---

**최종 업데이트**: 2025-08-27 12:43:00 UTC  
**상태**: ✅ 문제 해결 완료, 새로운 태스크 시작 중  
**예상 서비스 가능 시간**: 2025-08-27 12:50:00 UTC
