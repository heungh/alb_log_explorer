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
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id, MaxResults=15)
        for i, row in enumerate(results['ResultSet']['Rows']):
            if i == 0:
                headers = [col.get('VarCharValue', '') for col in row['Data']]
                print(f"  {' | '.join(headers)}")
                print(f"  {'-' * (len(' | '.join(headers)) + 10)}")
            else:
                values = [col.get('VarCharValue', '') for col in row['Data']]
                print(f"  {' | '.join(values)}")

def main():
    # 1. 포트 사용 패턴 분석 (봇 탐지)
    port_analysis = """
    SELECT 
        regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
        COUNT(DISTINCT regexp_extract(client_ip_port, ':([0-9]+)', 1)) as unique_ports,
        COUNT(*) as total_requests,
        ROUND(COUNT(*) / COUNT(DISTINCT regexp_extract(client_ip_port, ':([0-9]+)', 1)), 2) as requests_per_port
    FROM accesslog_analytics.access_logs
    WHERE client_ip_port IS NOT NULL
    GROUP BY 1
    ORDER BY unique_ports DESC;
    """
    run_query(port_analysis, "포트 사용 패턴 분석 (봇 탐지)")
    
    # 2. 시간당 요청 분포 (정상 vs 비정상 패턴)
    hourly_pattern = """
    SELECT 
        regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
        HOUR(from_unixtime(CAST(response_time1 AS bigint)/1000)) as hour_estimate,
        COUNT(*) as request_count
    FROM accesslog_analytics.access_logs
    WHERE client_ip_port IS NOT NULL AND response_time1 IS NOT NULL
    GROUP BY 1, 2
    ORDER BY 1, 2;
    """
    
    # 3. 가장 의심스러운 API 엔드포인트
    suspicious_endpoints = """
    SELECT 
        regexp_extract(request, '"[A-Z]+ ([^?]+)', 1) as base_url,
        COUNT(*) as request_count,
        COUNT(DISTINCT regexp_extract(client_ip_port, '^([^:]+)', 1)) as unique_ips,
        AVG(response_time1) as avg_response_time,
        CASE 
            WHEN COUNT(*) > 100000 THEN 'HIGH_VOLUME'
            WHEN AVG(response_time1) > 3000 THEN 'SLOW_RESPONSE'
            WHEN COUNT(DISTINCT regexp_extract(client_ip_port, '^([^:]+)', 1)) = 1 THEN 'SINGLE_IP'
            ELSE 'NORMAL'
        END as risk_level
    FROM accesslog_analytics.access_logs
    WHERE request LIKE '"%' AND response_time1 IS NOT NULL
    GROUP BY 1
    ORDER BY request_count DESC
    LIMIT 15;
    """
    run_query(suspicious_endpoints, "의심스러운 API 엔드포인트 분석")
    
    # 4. 데이터 손실 패턴 분석
    data_loss_pattern = """
    SELECT 
        CASE 
            WHEN client_ip_port IS NULL AND request IS NULL AND response_time1 IS NULL THEN 'All_NULL'
            WHEN client_ip_port IS NOT NULL AND request IS NULL THEN 'Request_NULL'
            WHEN client_ip_port IS NULL AND request IS NOT NULL THEN 'IP_NULL'
            ELSE 'Partial_Data'
        END as data_pattern,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage
    FROM accesslog_analytics.access_logs
    GROUP BY 1
    ORDER BY count DESC;
    """
    run_query(data_loss_pattern, "데이터 손실 패턴 분석")

if __name__ == "__main__":
    main()
