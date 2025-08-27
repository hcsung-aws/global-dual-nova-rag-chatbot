# Global Dual Nova RAG Chatbot 배포 히스토리

## 📅 배포 일자: 2025-08-27
## 🕐 작업 시간: 13:01 - 13:14 UTC (약 13분)
## 👤 작업자: hcsung
## 🌍 리전: ap-northeast-1 (도쿄)

---

## 🎯 배포 목표
- Global Dual Nova RAG Chatbot의 ECS 배포 문제 해결
- 컨테이너 시작 실패 원인 분석 및 수정
- 애플리케이션 정상 작동 확인

---

## 📊 초기 상태 (13:01 UTC)
- **ECS 서비스**: dual-nova-chatbot-production-service
- **클러스터**: dual-nova-chatbot-production-cluster
- **태스크 정의**: dual-nova-chatbot-production-task:4
- **상태**: 
  - Running Count: 0
  - Desired Count: 1
  - Failed Tasks: 0
  - Rollout State: IN_PROGRESS

---

## 🔍 문제 진단 과정

### 1단계: ECS 서비스 상태 모니터링 (13:01-13:08 UTC)
- **5분 간격 모니터링** 실시
- **지속적인 문제**: runningCount=0, 태스크 시작 실패 반복
- **관찰된 패턴**: 태스크가 시작되지만 곧 실패하여 재시작

### 2단계: 실패한 태스크 분석 (13:08 UTC)
- **실패한 태스크들**:
  - `b70518fbab2a4e37a325499ad055c834`
  - `72450888207048b79e074b767669c1f3`
- **태스크 상태**: 
  - Last Status: DEPROVISIONING
  - Stopped Reason: "Essential container in task exited"
  - Exit Code: 1

### 3단계: CloudWatch 로그 분석 (13:08 UTC)
- **로그 그룹**: `/ecs/dual-nova-chatbot-production`
- **핵심 발견**: 
  ```
  fatal error: An error occurred (403) when calling the HeadObject operation: Forbidden
  ```
- **문제 식별**: S3 권한 문제로 소스 코드 다운로드 실패

---

## 🛠️ 문제 해결 과정

### 1단계: IAM 정책 분석
- **문제점**: ECS 태스크 역할의 S3 권한 설정 오류
- **기존 설정**: `Resource = var.s3_bucket_arns` (버킷 ARN만 포함)
- **필요한 설정**: S3 객체 접근을 위한 `버킷ARN/*` 형태 필요

### 2단계: Terraform 코드 수정 (13:09 UTC)
**파일**: `/terraform/modules/security/main.tf`

**수정 전**:
```hcl
{
  Effect = "Allow"
  Action = [
    "s3:GetObject",
    "s3:PutObject"
  ]
  Resource = var.s3_bucket_arns
}
```

**수정 후**:
```hcl
{
  Effect = "Allow"
  Action = [
    "s3:GetObject",
    "s3:PutObject"
  ]
  Resource = [for arn in var.s3_bucket_arns : "${arn}/*"]
}
```

### 3단계: Terraform 적용 (13:09 UTC)
```bash
cd /home/hcsung/global-dual-nova-rag-chatbot/terraform
terraform apply -auto-approve
```

**결과**: IAM 정책 성공적으로 업데이트
- S3 객체 접근 권한 추가: `arn:aws:s3:::dual-nova-chatbot-production-code-62eea701/*`

### 4단계: ECS 서비스 강제 업데이트 (13:10 UTC)
```bash
aws ecs update-service --cluster dual-nova-chatbot-production-cluster --service dual-nova-chatbot-production-service
```

---

## ✅ 해결 결과

### 새로운 태스크 성공 (13:10 UTC)
- **새 태스크 ID**: `f5adb21cedae44fc80eb34598004f2b5`
- **시작 시간**: 22:09:55 (한국시간)
- **타겟 그룹 등록**: 22:10:36 (한국시간)

### S3 다운로드 성공 확인
**CloudWatch 로그**:
```
Downloading requirements...
download: s3://dual-nova-chatbot-production-code-62eea701/requirements.txt to tmp/requirements.txt
Installing Python packages...
```

### 애플리케이션 정상 작동 확인 (13:13 UTC)
```bash
curl -I http://dual-nova-chatbot-production-alb-2134834621.ap-northeast-1.elb.amazonaws.com
```

**응답**:
```
HTTP/1.1 200 OK
Server: TornadoServer/6.5.2
Content-Type: text/html
Content-Length: 1522
```

---

## 📈 최종 상태 (13:14 UTC)

### ECS 서비스 상태
- ✅ **Running Count**: 1
- ✅ **Desired Count**: 1
- ✅ **Failed Tasks**: 0
- ✅ **Rollout State**: IN_PROGRESS → STABLE

### 애플리케이션 접속
- ✅ **URL**: http://dual-nova-chatbot-production-alb-2134834621.ap-northeast-1.elb.amazonaws.com
- ✅ **상태**: HTTP 200 OK
- ✅ **서버**: TornadoServer/6.5.2 (Streamlit)

---

## 🔧 기술적 세부사항

### 인프라 구성
- **컨테이너 이미지**: python:3.11-slim
- **CPU**: 512
- **메모리**: 1024MB
- **네트워크**: Private 서브넷 (NAT Gateway 경유)
- **로드 밸런서**: Application Load Balancer
- **헬스체크**: 600초 grace period, 90초 간격

### 보안 설정
- **IAM 역할**: 
  - ECS Task Execution Role
  - ECS Task Role (S3, Bedrock, Secrets Manager 권한)
- **시크릿 관리**: AWS Secrets Manager
- **네트워크**: VPC, Private 서브넷, Security Groups

### 모니터링
- **로그**: CloudWatch Logs (`/ecs/dual-nova-chatbot-production`)
- **메트릭**: ECS 서비스 메트릭, ALB 메트릭
- **태그**: 표준화된 리소스 태깅

---

## 📚 학습 포인트

### 1. IAM 권한 설정의 중요성
- S3 버킷 접근과 객체 접근은 별도 권한 필요
- `arn:aws:s3:::bucket-name` vs `arn:aws:s3:::bucket-name/*`

### 2. 컨테이너 로그 분석
- CloudWatch Logs를 통한 실시간 디버깅
- Exit Code 1은 애플리케이션 레벨 오류를 의미

### 3. ECS 배포 패턴
- Health Check Grace Period의 중요성
- 태스크 재시작 패턴 분석을 통한 문제 진단

### 4. Terraform 모듈화의 장점
- 보안 모듈 분리로 권한 관리 용이
- 코드 재사용성과 유지보수성 향상

---

## 🚀 다음 단계

### 즉시 수행 가능
1. **기능 테스트**: 챗봇 기능 전체 테스트
2. **성능 모니터링**: 응답 시간, 리소스 사용량 확인
3. **보안 검토**: 추가 보안 설정 검토

### 향후 개선사항
1. **HTTPS 설정**: SSL 인증서 적용
2. **도메인 연결**: Route 53을 통한 사용자 친화적 URL
3. **오토스케일링**: 트래픽 기반 자동 확장 설정
4. **백업 전략**: 설정 및 데이터 백업 계획

---

## 📞 연락처 및 참고자료

### 프로젝트 정보
- **저장소**: https://github.com/hcsung-aws/global-dual-nova-rag-chatbot
- **문서**: `/docs` 디렉토리 참조
- **아키텍처**: 모듈화된 Terraform 구조

### 리소스 정보
- **AWS 계정**: 965037532757
- **리전**: ap-northeast-1
- **환경**: production
- **프로젝트 태그**: dual-nova-chatbot

---

**배포 완료 시간**: 2025-08-27 13:14 UTC  
**총 소요 시간**: 13분  
**상태**: ✅ 성공적으로 배포 완료
