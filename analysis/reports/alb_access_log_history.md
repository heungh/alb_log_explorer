# ALB 액세스 로그 분석 히스토리

## 📊 ALB 액세스 로그 설정 및 분석 결과

### 🔧 설정 정보
- **분석 일시:** 2025-08-31 07:03-07:11 UTC
- **ALB 이름:** alb-match
- **ALB ARN:** arn:aws:elasticloadbalancing:ap-northeast-2:181136804328:loadbalancer/app/alb-match/f895263fb0246bf5
- **로그 버킷:** alb-access-logs-20250819
- **로그 프리픽스:** alb-match

### 📁 로그 파일 정보
- **파일명:** 181136804328_elasticloadbalancing_ap-northeast-2_app.alb-match.f895263fb0246bf5_20250831T0705Z_15.165.114.31_kkuwr68o.log.gz
- **파일 크기:** 405 bytes
- **로그 엔트리 수:** 1개

### 🎯 발견된 클라이언트 요청 정보

#### 📊 요청 상세 분석
- **🕐 요청 시간:** 2025-08-31T07:03:31.828037Z
- **🔗 프로토콜:** HTTPS
- **🖥️ 클라이언트 IP:** 15.235.227.163:44410
- **🎯 타겟:** - (연결 실패)
- **📈 상태코드:** 503 (Service Unavailable)
- **📊 바이트:** 수신=151, 송신=337

#### 🌐 HTTP 요청 정보
- **🌍 HTTP 메소드:** GET
- **🛤️ 요청 경로:** `/` (루트 경로)
- **📋 HTTP 버전:** HTTP/1.1
- **🔗 전체 URL:** https://15.165.114.31:443/

#### 🤖 클라이언트 정보
- **User-Agent:** Mozilla/5.0 (compatible; ModatScanner/1.1; +https://modat.io/)
- **클라이언트 유형:** 보안 스캐너 봇 (ModatScanner)

#### 🔐 보안 정보
- **TLS 버전:** TLSv1.3
- **암호화 방식:** TLS_AES_128_GCM_SHA256
- **인증서 ARN:** arn:aws:acm:ap-northeast-2:181136804328:certificate/0d41432d-dde6-4ce5-a835-e0652b38f992

### 📈 요약 통계

#### 요청 경로별 접근 횟수
| 횟수 | 경로 | 메소드 | 상태코드 |
|------|------|--------|----------|
| 1회  | `/`  | GET    | 503      |

### 🔍 분석 결과

1. **요청 패턴**: 클라이언트가 ALB의 **루트 경로 (`/`)**에 HTTPS로 접근
2. **연결 상태**: 503 오류로 백엔드 서버 연결 실패
3. **클라이언트 유형**: 자동화된 보안 검사 도구 (ModatScanner)
4. **보안**: TLSv1.3을 사용한 안전한 암호화 연결 시도

### 🛠️ 사용된 분석 명령어

#### ALB 로그 활성화
```bash
aws elbv2 modify-load-balancer-attributes \
    --load-balancer-arn arn:aws:elasticloadbalancing:ap-northeast-2:181136804328:loadbalancer/app/alb-match/f895263fb0246bf5 \
    --attributes \
        Key=access_logs.s3.enabled,Value=true \
        Key=access_logs.s3.bucket,Value=alb-access-logs-20250819 \
        Key=access_logs.s3.prefix,Value=alb-match \
    --region ap-northeast-2
```

#### 로그 파일 분석
```bash
# 로그 파일 다운로드
aws s3 cp s3://alb-access-logs-20250819/alb-match/AWSLogs/181136804328/elasticloadbalancing/ap-northeast-2/2025/08/31/ . --recursive

# 압축 해제 및 분석
gunzip *.gz
cat *.log

# 요청 경로 추출
awk '{match($0, /"[A-Z]+ ([^ ]+) HTTP/); if(RSTART) print substr($0, RSTART, RLENGTH)}' *.log
```

### 📋 로그 필드 구조

ALB 액세스 로그의 주요 필드:
1. type (https)
2. timestamp (2025-08-31T07:03:31.828037Z)
3. elb (app/alb-match/f895263fb0246bf5)
4. client:port (15.235.227.163:44410)
5. target:port (-)
6. request_processing_time (-1)
7. target_processing_time (-1)
8. response_processing_time (-1)
9. elb_status_code (503)
10. target_status_code (-)
11. received_bytes (151)
12. sent_bytes (337)
13. request ("GET https://15.165.114.31:443/ HTTP/1.1")
14. user_agent ("Mozilla/5.0 (compatible; ModatScanner/1.1; +https://modat.io/)")
15. ssl_cipher (TLS_AES_128_GCM_SHA256)
16. ssl_protocol (TLSv1.3)

### 💡 향후 분석 방향

1. **트래픽 증가 시**: 더 다양한 경로 패턴 분석 가능
2. **Athena 활용**: 대용량 로그 데이터 SQL 쿼리 분석
3. **CloudWatch Insights**: 실시간 로그 모니터링 및 알람 설정
4. **보안 분석**: 비정상적인 접근 패턴 탐지

## 🔍 ALB 경로 구분 능력 상세 분석

### ✅ ALB가 정확히 구분할 수 있는 것들:

#### 1. 기본 경로 구분
- `/`, `/home`, `/about` 등 모든 경로 레벨
- `/api/v1/users`, `/api/v1/users/123`, `/api/v1/users/123/profile`

#### 2. HTTP 메소드별 구분
```
"GET /api/users HTTP/1.1"
"POST /api/users HTTP/1.1"  
"PUT /api/users/123 HTTP/1.1"
"DELETE /api/users/123 HTTP/1.1"
```

#### 3. 쿼리 파라미터 완전 포함
```
"GET /search?q=aws&category=cloud&page=1 HTTP/1.1"
"GET /products?page=2&limit=20&sort=price HTTP/1.1"
"GET /api/users?filter=active&role=admin HTTP/1.1"
```

#### 4. 정적 리소스
```
"GET /images/logo.png HTTP/1.1"
"GET /css/bootstrap.min.css HTTP/1.1"
"GET /js/app.js HTTP/1.1"
"GET /favicon.ico HTTP/1.1"
```

#### 5. 특수 문자 및 인코딩
```
"GET /path/with%20spaces HTTP/1.1"
"GET /korean/한글경로 HTTP/1.1"
"GET /special/path-with_underscore HTTP/1.1"
```

### 📊 경로 분석 예시 결과

#### 모든 요청 경로 목록:
| 메소드 | 경로 |
|--------|------|
| GET | / |
| GET | /api/users |
| GET | /api/users/123 |
| POST | /api/users/123/profile |
| GET | /images/logo.png |
| GET | /search?q=aws&category=cloud&page=1 |
| GET | /nonexistent/path |

#### HTTP 메소드별 분류:
- **GET**: 6회
- **POST**: 1회

#### API 경로만 필터링:
- GET /api/users
- GET /api/users/123  
- POST /api/users/123/profile

## 🖥️ AWS 웹 콘솔에서 ALB 로그 확인 방법

### 1. 📊 Athena Console (가장 강력한 방법)

#### ALB 로그 테이블 생성 SQL:
```sql
CREATE EXTERNAL TABLE alb_access_logs (
    type string,
    time string,
    elb string,
    client_ip string,
    client_port int,
    target_ip string,
    target_port int,
    request_processing_time double,
    target_processing_time double,
    response_processing_time double,
    elb_status_code int,
    target_status_code string,
    received_bytes bigint,
    sent_bytes bigint,
    request string,
    user_agent string,
    ssl_cipher string,
    ssl_protocol string,
    target_group_arn string,
    trace_id string,
    domain_name string,
    chosen_cert_arn string,
    matched_rule_priority int,
    request_creation_time string,
    actions_executed string,
    redirect_url string,
    lambda_error_reason string,
    target_port_list string,
    target_status_code_list string,
    classification string,
    classification_reason string
)
PARTITIONED BY(
    year string,
    month string,
    day string
)
STORED AS INPUTFORMAT 
    'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
    'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://alb-access-logs-20250819/alb-match/AWSLogs/181136804328/elasticloadbalancing/ap-northeast-2/'
TBLPROPERTIES (
    'projection.enabled'='true',
    'projection.year.type'='integer',
    'projection.year.range'='2020,2030',
    'projection.month.type'='integer',
    'projection.month.range'='1,12',
    'projection.month.digits'='2',
    'projection.day.type'='integer',
    'projection.day.range'='1,31',
    'projection.day.digits'='2',
    'storage.location.template'='s3://alb-access-logs-20250819/alb-match/AWSLogs/181136804328/elasticloadbalancing/ap-northeast-2/${year}/${month}/${day}/'
);
```

#### 요청 경로별 분석 쿼리:
```sql
SELECT 
    regexp_extract(request, '^(\w+)\s+([^\s]+)\s+', 2) as request_path,
    regexp_extract(request, '^(\w+)\s+', 1) as method,
    COUNT(*) as request_count,
    AVG(target_processing_time) as avg_response_time,
    elb_status_code
FROM alb_access_logs 
WHERE year='2025' AND month='08' AND day='31'
GROUP BY 
    regexp_extract(request, '^(\w+)\s+([^\s]+)\s+', 2),
    regexp_extract(request, '^(\w+)\s+', 1),
    elb_status_code
ORDER BY request_count DESC
LIMIT 20;
```

### 2. 📈 CloudWatch Logs Insights

#### 접근 방법:
1. **AWS Console → CloudWatch → Logs → Insights**
2. 로그 그룹 선택: `/aws/applicationloadbalancer/alb-match`

#### 쿼리 예시:
```sql
fields @timestamp, request
| filter request like /GET/
| stats count() by request
| sort count desc
| limit 20
```

```sql
fields @timestamp, request, elb_status_code
| filter elb_status_code >= 400
| stats count() by request
| sort count desc
```

### 3. 🗂️ S3 Console

#### 접근 경로:
1. **AWS Console → S3 → alb-access-logs-20250819**
2. **alb-match/AWSLogs/181136804328/elasticloadbalancing/ap-northeast-2/**
3. 로그 파일 다운로드 후 로컬에서 분석

### 4. 📊 CloudWatch Dashboard

#### 생성된 대시보드:
- **대시보드명**: ALB-Access-Logs-Dashboard
- **위치**: AWS Console → CloudWatch → Dashboards

#### 대시보드 쿼리:
```sql
SOURCE '/aws/applicationloadbalancer/alb-match'
| fields @timestamp, request
| filter request like /GET/
| stats count() by bin(5m)
```

### 🎯 웹 콘솔 접근 방법 요약

#### ✅ 즉시 사용 가능한 방법들:

1. **Athena** (가장 강력)
   - SQL 쿼리로 상세 분석
   - 경로별 통계, 응답시간, 오류율 분석

2. **CloudWatch Logs Insights**
   - 실시간 로그 검색/분석
   - 필터링 및 집계 기능

3. **CloudWatch Dashboard**
   - 시각적 대시보드
   - 실시간 모니터링

4. **S3 Console**
   - 원본 파일 다운로드
   - 수동 분석

#### 🚀 권장 사용법:
- **일회성 분석**: Athena Console
- **실시간 모니터링**: CloudWatch Logs Insights
- **지속적 모니터링**: CloudWatch Dashboard

### 💡 추가 분석 쿼리 예시

#### 가장 많이 접근되는 경로 TOP 10:
```sql
SELECT 
    regexp_extract(request, '^[A-Z]+\s+([^\s\?]+)', 1) as path,
    COUNT(*) as count
FROM alb_access_logs 
WHERE year='2025' AND month='08' AND day='31'
GROUP BY regexp_extract(request, '^[A-Z]+\s+([^\s\?]+)', 1)
ORDER BY count DESC
LIMIT 10;
```

#### 404 오류가 발생한 경로들:
```sql
SELECT 
    regexp_extract(request, '^[A-Z]+\s+([^\s]+)', 1) as path,
    COUNT(*) as error_count
FROM alb_access_logs 
WHERE elb_status_code = 404
    AND year='2025' AND month='08' AND day='31'
GROUP BY regexp_extract(request, '^[A-Z]+\s+([^\s]+)', 1)
ORDER BY error_count DESC;
```

#### 응답 시간이 긴 경로 분석:
```sql
SELECT 
    regexp_extract(request, '^[A-Z]+\s+([^\s\?]+)', 1) as path,
    AVG(target_processing_time) as avg_response_time,
    MAX(target_processing_time) as max_response_time,
    COUNT(*) as request_count
FROM alb_access_logs 
WHERE target_processing_time > 0
    AND year='2025' AND month='08' AND day='31'
GROUP BY regexp_extract(request, '^[A-Z]+\s+([^\s\?]+)', 1)
ORDER BY avg_response_time DESC
LIMIT 10;
```

---
*분석 완료: 2025-08-31 07:13 UTC*
