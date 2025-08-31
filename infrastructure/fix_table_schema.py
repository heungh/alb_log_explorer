#!/usr/bin/env python3
import boto3

# AWS 클라이언트 초기화
region = 'ap-northeast-2'
glue_client = boto3.client('glue', region_name=region)

DATABASE_NAME = 'accesslog_analytics'
TABLE_NAME = 'access_logs'
BUCKET_NAME = 'hhs-test3'

def delete_existing_table():
    """기존 테이블 삭제"""
    try:
        glue_client.delete_table(
            DatabaseName=DATABASE_NAME,
            Name=TABLE_NAME
        )
        print(f"Deleted existing table: {TABLE_NAME}")
    except glue_client.exceptions.EntityNotFoundException:
        print(f"Table {TABLE_NAME} does not exist")

def create_custom_log_table():
    """실제 로그 형식에 맞는 테이블 생성"""
    table_input = {
        'Name': TABLE_NAME,
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'client_ip_port', 'Type': 'string'},
                {'Name': 'response_time1', 'Type': 'int'},
                {'Name': 'response_time2', 'Type': 'int'},
                {'Name': 'request', 'Type': 'string'}
            ],
            'Location': f's3://{BUCKET_NAME}/raw-data/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.RegexSerDe',
                'Parameters': {
                    'input.regex': '([^\\t]*)\\t([^\\t]*)\\t([^\\t]*)\\t(.*)'
                }
            }
        },
        'PartitionKeys': [],
        'TableType': 'EXTERNAL_TABLE'
    }
    
    glue_client.create_table(
        DatabaseName=DATABASE_NAME,
        TableInput=table_input
    )
    print(f"Created new table: {TABLE_NAME}")

def create_updated_queries():
    """업데이트된 쿼리 생성"""
    queries = {
        'basic_stats.sql': """
-- 기본 통계
SELECT 
    COUNT(*) as total_requests,
    COUNT(DISTINCT regexp_extract(client_ip_port, '^([^:]+)', 1)) as unique_ips,
    AVG(response_time1) as avg_response_time1,
    AVG(response_time2) as avg_response_time2
FROM accesslog_analytics.access_logs;
""",
        'top_ips_updated.sql': """
-- 상위 클라이언트 IP 분석 (업데이트됨)
SELECT 
    regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
    COUNT(*) as request_count,
    AVG(response_time1) as avg_response_time1,
    AVG(response_time2) as avg_response_time2
FROM accesslog_analytics.access_logs
GROUP BY regexp_extract(client_ip_port, '^([^:]+)', 1)
ORDER BY request_count DESC
LIMIT 20;
""",
        'request_analysis.sql': """
-- 요청 분석
SELECT 
    regexp_extract(request, '"(GET|POST|PUT|DELETE)', 1) as http_method,
    COUNT(*) as request_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage
FROM accesslog_analytics.access_logs
WHERE request LIKE '"%'
GROUP BY regexp_extract(request, '"(GET|POST|PUT|DELETE)', 1)
ORDER BY request_count DESC;
""",
        'response_time_analysis.sql': """
-- 응답 시간 분석
SELECT 
    CASE 
        WHEN response_time1 < 1000 THEN 'Fast (<1s)'
        WHEN response_time1 < 3000 THEN 'Medium (1-3s)'
        WHEN response_time1 < 5000 THEN 'Slow (3-5s)'
        ELSE 'Very Slow (>5s)'
    END as response_category,
    COUNT(*) as request_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage,
    AVG(response_time1) as avg_response_time
FROM accesslog_analytics.access_logs
WHERE response_time1 IS NOT NULL
GROUP BY 1
ORDER BY avg_response_time;
"""
    }
    
    for filename, query in queries.items():
        with open(filename, 'w') as f:
            f.write(query)
        print(f"Created updated query file: {filename}")

def main():
    print("=== 테이블 스키마 수정 ===")
    
    # 1. 기존 테이블 삭제
    print("\n1. Deleting existing table...")
    delete_existing_table()
    
    # 2. 새 테이블 생성
    print("\n2. Creating new table with correct schema...")
    create_custom_log_table()
    
    # 3. 업데이트된 쿼리 생성
    print("\n3. Creating updated queries...")
    create_updated_queries()
    
    print("\n=== 수정 완료 ===")
    print("이제 Athena에서 새로운 쿼리들을 실행할 수 있습니다.")

if __name__ == "__main__":
    main()
