# 🛡️ 보안 설정 가이드

이 문서는 Global Dual Nova RAG Chatbot의 보안 설정 방법을 설명합니다.

## 📋 목차

- [개요](#개요)
- [보안 설정 옵션](#보안-설정-옵션)
- [배포 시나리오별 설정](#배포-시나리오별-설정)
- [IP 주소 확인 방법](#ip-주소-확인-방법)
- [보안 모범 사례](#보안-모범-사례)
- [문제 해결](#문제-해결)

## 개요

기본적으로 이 애플리케이션은 **공개 접근**이 가능하도록 설정되어 있습니다. 프로덕션 환경에서는 **반드시 접근을 제한**해야 합니다.

## 보안 설정 옵션

### 🔓 옵션 1: 공개 접근 (개발 환경용)

```hcl
# terraform.tfvars
restrict_public_access = false
allowed_cidr_blocks    = ["0.0.0.0/0"]
```

**⚠️ 경고**: 프로덕션 환경에서는 사용하지 마세요!

### 🔒 옵션 2: 제한된 접근 (권장)

```hcl
# terraform.tfvars
restrict_public_access = true
admin_ip_addresses     = [
  "203.0.113.1",    # 사무실 IP
  "198.51.100.1",   # 집 IP
  "192.0.2.1"       # VPN IP
]
```

### 🏢 옵션 3: 네트워크 기반 접근

```hcl
# terraform.tfvars
restrict_public_access = false
allowed_cidr_blocks    = [
  "10.0.0.0/8",      # 사내 네트워크
  "172.16.0.0/12",   # VPN 네트워크
  "192.168.0.0/16"   # 로컬 네트워크
]
```

### 🎛️ 옵션 4: 커스텀 규칙

```hcl
# terraform.tfvars
custom_access_rules = [
  {
    description = "사무실 네트워크 HTTP"
    cidr_block  = "203.0.113.0/24"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
  },
  {
    description = "VPN 네트워크 HTTPS"
    cidr_block  = "198.51.100.0/24"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
  }
]
```

## 배포 시나리오별 설정

### 🧪 개발 환경

```hcl
# terraform.tfvars
environment = "development"
restrict_public_access = false
allowed_cidr_blocks = ["0.0.0.0/0"]
enable_vpc_access = true
```

### 🏭 프로덕션 환경

```hcl
# terraform.tfvars
environment = "production"
restrict_public_access = true
admin_ip_addresses = ["YOUR.IP.ADDRESS.HERE"]
enable_https = true
ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id"
```

### 🏢 기업 환경

```hcl
# terraform.tfvars
environment = "corporate"
restrict_public_access = false
allowed_cidr_blocks = ["203.0.113.0/24"]  # 회사 네트워크
custom_access_rules = [
  {
    description = "본사 네트워크"
    cidr_block  = "203.0.113.0/24"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
  },
  {
    description = "지사 네트워크"
    cidr_block  = "198.51.100.0/24"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
  }
]
```

## IP 주소 확인 방법

### 현재 IP 주소 확인

```bash
# 방법 1: curl 사용
curl https://ipinfo.io/ip

# 방법 2: 웹 브라우저
# https://whatismyipaddress.com/ 방문

# 방법 3: AWS CLI (AWS 환경에서)
curl https://checkip.amazonaws.com/
```

### 네트워크 CIDR 확인

```bash
# 현재 네트워크 정보 확인
ip route | grep default

# 또는
route -n | grep UG
```

## 보안 모범 사례

### ✅ 권장사항

1. **최소 권한 원칙**
   - 필요한 IP/네트워크만 허용
   - 불필요한 포트는 차단

2. **정기적인 검토**
   - 월 1회 접근 권한 검토
   - 불필요한 IP 제거

3. **HTTPS 사용**
   - 프로덕션에서는 반드시 HTTPS 활성화
   - 유효한 SSL 인증서 사용

4. **모니터링**
   - CloudWatch 로그 활성화
   - 비정상적인 접근 패턴 모니터링

### ❌ 피해야 할 것

1. **공개 접근 유지**
   - `0.0.0.0/0` 프로덕션 사용 금지

2. **하드코딩된 IP**
   - 동적 IP 환경에서 주의

3. **HTTP 사용**
   - 프로덕션에서 HTTP 사용 금지

## 문제 해결

### 접근이 안 될 때

1. **IP 주소 확인**
   ```bash
   curl https://ipinfo.io/ip
   ```

2. **보안 그룹 확인**
   ```bash
   aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx
   ```

3. **로드 밸런서 상태 확인**
   ```bash
   aws elbv2 describe-load-balancers
   ```

### 일반적인 오류

#### 1. Connection Timeout
- **원인**: IP가 허용 목록에 없음
- **해결**: `admin_ip_addresses`에 현재 IP 추가

#### 2. 403 Forbidden
- **원인**: 보안 그룹 규칙 문제
- **해결**: 보안 그룹 규칙 재확인

#### 3. 502 Bad Gateway
- **원인**: ECS 태스크 문제
- **해결**: ECS 서비스 상태 확인

### 긴급 접근 복구

공개 접근으로 임시 복구:

```bash
# 보안 그룹에 임시 규칙 추가
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

**⚠️ 주의**: 문제 해결 후 즉시 제거하세요!

## 설정 예제

### 완전한 terraform.tfvars 예제

```hcl
# 기본 설정
aws_region = "us-east-1"
environment = "production"
project_name = "global-dual-nova-chatbot"

# 보안 설정 (프로덕션)
restrict_public_access = true
admin_ip_addresses = [
  "203.0.113.1",    # 사무실 IP
  "198.51.100.1"    # 집 IP
]

# HTTPS 설정
enable_https = true
ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id"

# Knowledge Base 설정
knowledge_base_id = "XXXXXXXXXX"

# 태그
tags = {
  Environment = "production"
  Owner = "DevOps Team"
  Project = "Global Dual Nova Chatbot"
  Security = "Restricted"
}
```

## 추가 보안 고려사항

### WAF (Web Application Firewall)

고급 보안이 필요한 경우 AWS WAF 추가 고려:

```hcl
# 추후 WAF 통합 예정
resource "aws_wafv2_web_acl" "main" {
  name  = "${var.project_name}-waf"
  scope = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  rule {
    name     = "RateLimitRule"
    priority = 1
    
    action {
      block {}
    }
    
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }
}
```

### VPN 통합

기업 환경에서는 VPN 통합 고려:

1. **AWS Client VPN**
2. **Site-to-Site VPN**
3. **Direct Connect**

---

**보안은 지속적인 과정입니다. 정기적으로 설정을 검토하고 업데이트하세요.**
