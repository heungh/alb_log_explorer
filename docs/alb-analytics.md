# ALB Access Log 분석 솔루션 배포 완료

## 🎯 배포 결과

### 인프라 구성
- **리전**: ap-northeast-2
- **S3 버킷**: alb-logs-analytics-1756017037
- **Glue 데이터베이스**: alb_analytics
- **Glue 테이블**: access_logs
- **Athena 워크그룹**: alb-analytics

### 데이터 현황
- **총 요청 수**: 3,659,312건
- **성공 요청 (200)**: 1,825,251건 (49.9%)
- **캐시 히트 (304)**: 3,953건 (0.1%)
- **에러 (404)**: 370건 (0.01%)
- **기타 상태코드**: 460, 201, 301, 302

### 주요 클라이언트 IP 분석
1. **13.124.46.40**: 1,815,063 요청 (평균 응답시간: 15.3ms, 총 트래픽: 17.3GB)
2. **140.248.29.3**: 14,216 요청 (평균 응답시간: 22.1ms, 총 트래픽: 178MB)

## 🔍 분석 쿼리 예제

### 1. 기본 통계
```sql
SELECT 
    COUNT(*) as total_requests,
    COUNT(DISTINCT client_ip) as unique_ips,
    AVG(request_processing_time + target_processing_time + response_processing_time) as avg_response_time
FROM alb_analytics.access_logs;
```

### 2. 상위 IP 분석
```sql
SELECT 
    client_ip,
    COUNT(*) as request_count,
    AVG(request_processing_time + target_processing_time + response_processing_time) as avg_response_time,
    SUM(received_bytes + sent_bytes) as total_bytes
FROM alb_analytics.access_logs
WHERE elb_status_code < 400 AND client_ip IS NOT NULL
GROUP BY client_ip
ORDER BY request_count DESC
LIMIT 10;
```

### 3. 에러 분석
```sql
SELECT 
    elb_status_code,
    COUNT(*) as error_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM alb_analytics.access_logs), 2) as error_percentage
FROM alb_analytics.access_logs
WHERE elb_status_code >= 400
GROUP BY elb_status_code
ORDER BY error_count DESC;
```

## 🚀 다음 단계

1. **실시간 모니터링**: CloudWatch 알람 설정
2. **자동화**: Lambda 함수로 정기 분석
3. **시각화**: QuickSight 대시보드 구성
4. **보안**: WAF 규칙 자동 업데이트

## 📊 접근 방법

### AWS 콘솔에서 확인
1. Athena 콘솔 → 워크그룹 'alb-analytics' 선택
2. 쿼리 에디터에서 위 SQL 실행
3. S3에서 결과 파일 확인

### CLI에서 확인
```bash
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM alb_analytics.access_logs" \
  --result-configuration OutputLocation=s3://alb-logs-analytics-1756017037/athena-results/ \
  --work-group alb-analytics \
  --region ap-northeast-2
```

배포가 성공적으로 완료되었습니다! 🎉
