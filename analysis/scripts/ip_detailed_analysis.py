#!/usr/bin/env python3
import boto3
import time

region = 'ap-northeast-2'
athena_client = boto3.client('athena', region_name=region)
WORKGROUP_NAME = 'accesslog-analytics'
ATHENA_RESULTS_BUCKET = f'aws-athena-query-results-{region}-181136804328'

def run_query(query, description):
    print(f"\n=== {description} ===")
    
    response = athena_client.start_query_execution(
        QueryString=query,
        ResultConfiguration={'OutputLocation': f's3://{ATHENA_RESULTS_BUCKET}/accesslog-analytics/'},
        WorkGroup=WORKGROUP_NAME
    )
    
    query_execution_id = response['QueryExecutionId']
    
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = response['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)
    
    if status == 'SUCCEEDED':
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id, MaxResults=20)
        for i, row in enumerate(results['ResultSet']['Rows']):
            if i == 0:
                headers = [col.get('VarCharValue', '') for col in row['Data']]
                print(f"  {' | '.join(headers)}")
                print(f"  {'-' * (len(' | '.join(headers)) + 10)}")
            else:
                values = [col.get('VarCharValue', '') for col in row['Data']]
                print(f"  {' | '.join(values)}")

def main():
    # 1. IP 지역 정보 확인 (AWS IP 대역인지)
    print("=== IP 13.124.46.40 지역 정보 ===")
    print("13.124.46.40은 AWS ap-northeast-2 (서울) 리전의 IP 대역입니다.")
    print("이는 AWS 서비스(ALB, CloudFront, EC2 등)에서 발생하는 트래픽일 가능성이 높습니다.")
    
    # 2. 포트 분포 패턴 분석
    port_distribution = """
    SELECT 
        regexp_extract(client_ip_port, ':([0-9]+)', 1) as port,
        COUNT(*) as request_count
    FROM accesslog_analytics.access_logs
    WHERE client_ip_port LIKE '13.124.46.40:%'
    GROUP BY 1
    ORDER BY request_count DESC
    LIMIT 15;
    """
    run_query(port_distribution, "13.124.46.40 포트 분포 (상위 15개)")
    
    # 3. 요청 간격 패턴 분석
    request_timing = """
    SELECT 
        response_time1,
        response_time2,
        COUNT(*) as frequency
    FROM accesslog_analytics.access_logs
    WHERE client_ip_port LIKE '13.124.46.40:%'
    GROUP BY 1, 2
    ORDER BY frequency DESC
    LIMIT 10;
    """
    run_query(request_timing, "13.124.46.40 응답시간 패턴")
    
    # 4. 140.248.29.3과 비교 분석
    comparison = """
    SELECT 
        regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
        COUNT(*) as total_requests,
        COUNT(DISTINCT regexp_extract(client_ip_port, ':([0-9]+)', 1)) as unique_ports,
        AVG(response_time1) as avg_response_time1,
        MIN(response_time1) as min_response_time1,
        MAX(response_time1) as max_response_time1,
        COUNT(DISTINCT regexp_extract(request, '"[A-Z]+ ([^ ]+)', 1)) as unique_urls
    FROM accesslog_analytics.access_logs
    WHERE client_ip_port IS NOT NULL
    GROUP BY 1;
    """
    run_query(comparison, "두 IP 비교 분석")
    
    # 5. 세션 API 호출 패턴 상세 분석
    session_pattern = """
    SELECT 
        regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
        response_time1,
        response_time2,
        COUNT(*) as frequency
    FROM accesslog_analytics.access_logs
    WHERE request LIKE '%/api/auth/session%'
    GROUP BY 1, 2, 3
    ORDER BY frequency DESC
    LIMIT 15;
    """
    run_query(session_pattern, "세션 API 호출 패턴 상세")
    
    # 6. 정상 vs 비정상 패턴 구분
    print("\n=== 정상 vs 비정상 패턴 분석 ===")
    print("정상 사용자 패턴:")
    print("- 포트: 1-10개 정도 사용")
    print("- 요청: 다양한 API 골고루 호출")
    print("- 시간: 불규칙한 간격")
    print("- 응답시간: 일정하지 않음")
    print()
    print("봇/자동화 패턴:")
    print("- 포트: 수천-수만개 체계적 사용")
    print("- 요청: 특정 API 반복 호출")
    print("- 시간: 규칙적인 간격")
    print("- 응답시간: 일정한 패턴")

if __name__ == "__main__":
    main()
