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
    else:
        print(f"Query failed: {status}")

def main():
    # 1. 가장 많이 호출된 URL 분석
    url_analysis = """
    SELECT 
        regexp_extract(request, '"[A-Z]+ ([^ ]+)', 1) as url_path,
        COUNT(*) as request_count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage,
        AVG(response_time1) as avg_response_time
    FROM accesslog_analytics.access_logs
    WHERE request LIKE '"%'
    GROUP BY regexp_extract(request, '"[A-Z]+ ([^ ]+)', 1)
    ORDER BY request_count DESC
    LIMIT 15;
    """
    run_query(url_analysis, "가장 많이 호출된 URL TOP 15")
    
    # 2. 비정상적으로 느린 요청들
    slow_requests = """
    SELECT 
        regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
        regexp_extract(request, '"[A-Z]+ ([^ ]+)', 1) as url_path,
        response_time1,
        response_time2,
        COUNT(*) as occurrence_count
    FROM accesslog_analytics.access_logs
    WHERE response_time1 > 10000
    GROUP BY 1, 2, 3, 4
    ORDER BY response_time1 DESC
    LIMIT 15;
    """
    run_query(slow_requests, "비정상적으로 느린 요청들 (>10초)")
    
    # 3. 특정 IP의 요청 패턴 분석
    ip_pattern = """
    SELECT 
        regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
        regexp_extract(request, '"([A-Z]+)', 1) as http_method,
        COUNT(*) as request_count,
        AVG(response_time1) as avg_response_time,
        MIN(response_time1) as min_response_time,
        MAX(response_time1) as max_response_time
    FROM accesslog_analytics.access_logs
    WHERE client_ip_port IS NOT NULL
    GROUP BY 1, 2
    ORDER BY request_count DESC;
    """
    run_query(ip_pattern, "IP별 요청 패턴 분석")
    
    # 4. 의심스러운 반복 요청 패턴
    suspicious_patterns = """
    SELECT 
        regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
        regexp_extract(request, '"[A-Z]+ ([^ ]+)', 1) as url_path,
        COUNT(*) as request_count,
        AVG(response_time1) as avg_response_time,
        COUNT(DISTINCT regexp_extract(client_ip_port, ':([0-9]+)', 1)) as unique_ports
    FROM accesslog_analytics.access_logs
    WHERE request LIKE '"%'
    GROUP BY 1, 2
    HAVING COUNT(*) > 1000
    ORDER BY request_count DESC
    LIMIT 20;
    """
    run_query(suspicious_patterns, "의심스러운 반복 요청 패턴 (>1000회)")
    
    # 5. 빈 데이터 분석
    empty_data = """
    SELECT 
        'Empty client_ip_port' as issue_type,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage
    FROM accesslog_analytics.access_logs
    WHERE client_ip_port IS NULL OR client_ip_port = ''
    UNION ALL
    SELECT 
        'Empty request' as issue_type,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage
    FROM accesslog_analytics.access_logs
    WHERE request IS NULL OR request = ''
    UNION ALL
    SELECT 
        'Null response_time1' as issue_type,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage
    FROM accesslog_analytics.access_logs
    WHERE response_time1 IS NULL;
    """
    run_query(empty_data, "데이터 품질 이슈 분석")

if __name__ == "__main__":
    main()
