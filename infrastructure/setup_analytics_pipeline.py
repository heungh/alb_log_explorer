#!/usr/bin/env python3
import boto3
import json
import os
import time
from datetime import datetime

# AWS 클라이언트 초기화
region = 'ap-northeast-2'
s3_client = boto3.client('s3', region_name=region)
glue_client = boto3.client('glue', region_name=region)
athena_client = boto3.client('athena', region_name=region)

# 설정
BUCKET_NAME = 'hhs-test3'
DATABASE_NAME = 'accesslog_analytics'
TABLE_NAME = 'access_logs'
ATHENA_RESULTS_BUCKET = f'aws-athena-query-results-{region}-181136804328'

def upload_txt_files():
    """현재 디렉토리의 txt 파일들을 S3에 업로드"""
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
    
    for file in txt_files:
        key = f'raw-data/{file}'
        print(f"Uploading {file} to s3://{BUCKET_NAME}/{key}")
        s3_client.upload_file(file, BUCKET_NAME, key)
    
    return txt_files

def create_glue_database():
    """Glue 데이터베이스 생성"""
    try:
        glue_client.create_database(
            DatabaseInput={
                'Name': DATABASE_NAME,
                'Description': 'Database for access log analytics'
            }
        )
        print(f"Created Glue database: {DATABASE_NAME}")
    except glue_client.exceptions.AlreadyExistsException:
        print(f"Database {DATABASE_NAME} already exists")

def create_glue_table():
    """Glue 테이블 생성 (ALB 액세스 로그 형식)"""
    table_input = {
        'Name': TABLE_NAME,
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'type', 'Type': 'string'},
                {'Name': 'time', 'Type': 'string'},
                {'Name': 'elb', 'Type': 'string'},
                {'Name': 'client_ip', 'Type': 'string'},
                {'Name': 'client_port', 'Type': 'int'},
                {'Name': 'target_ip', 'Type': 'string'},
                {'Name': 'target_port', 'Type': 'int'},
                {'Name': 'request_processing_time', 'Type': 'double'},
                {'Name': 'target_processing_time', 'Type': 'double'},
                {'Name': 'response_processing_time', 'Type': 'double'},
                {'Name': 'elb_status_code', 'Type': 'int'},
                {'Name': 'target_status_code', 'Type': 'string'},
                {'Name': 'received_bytes', 'Type': 'bigint'},
                {'Name': 'sent_bytes', 'Type': 'bigint'},
                {'Name': 'request', 'Type': 'string'},
                {'Name': 'user_agent', 'Type': 'string'},
                {'Name': 'ssl_cipher', 'Type': 'string'},
                {'Name': 'ssl_protocol', 'Type': 'string'},
                {'Name': 'target_group_arn', 'Type': 'string'},
                {'Name': 'trace_id', 'Type': 'string'},
                {'Name': 'domain_name', 'Type': 'string'},
                {'Name': 'chosen_cert_arn', 'Type': 'string'},
                {'Name': 'matched_rule_priority', 'Type': 'string'},
                {'Name': 'request_creation_time', 'Type': 'string'},
                {'Name': 'actions_executed', 'Type': 'string'},
                {'Name': 'redirect_url', 'Type': 'string'},
                {'Name': 'lambda_error_reason', 'Type': 'string'},
                {'Name': 'target_port_list', 'Type': 'string'},
                {'Name': 'target_status_code_list', 'Type': 'string'},
                {'Name': 'classification', 'Type': 'string'},
                {'Name': 'classification_reason', 'Type': 'string'}
            ],
            'Location': f's3://{BUCKET_NAME}/raw-data/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.RegexSerDe',
                'Parameters': {
                    'input.regex': '([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]* [^ ]* [^ ]*)\" \"([^\"]*)\" ([A-Z0-9-]+) ([A-Za-z0-9.-]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^\"]*)\" ([-.0-9]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^ ]*)\" \"([^\s]+?)\" \"([^\s]+)\" \"([^ ]*)\" \"([^ ]*)\""'
                }
            }
        },
        'PartitionKeys': [],
        'TableType': 'EXTERNAL_TABLE'
    }
    
    try:
        glue_client.create_table(
            DatabaseName=DATABASE_NAME,
            TableInput=table_input
        )
        print(f"Created Glue table: {TABLE_NAME}")
    except glue_client.exceptions.AlreadyExistsException:
        print(f"Table {TABLE_NAME} already exists")

def create_sample_queries():
    """샘플 Athena 쿼리 생성"""
    queries = {
        'top_ips.sql': """
-- 상위 클라이언트 IP 분석
SELECT 
    client_ip,
    COUNT(*) as request_count,
    AVG(request_processing_time + target_processing_time + response_processing_time) as avg_response_time,
    SUM(received_bytes + sent_bytes) as total_bytes
FROM accesslog_analytics.access_logs
WHERE elb_status_code < 400
GROUP BY client_ip
ORDER BY request_count DESC
LIMIT 20;
""",
        'error_analysis.sql': """
-- 에러 분석
SELECT 
    elb_status_code,
    COUNT(*) as error_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as error_percentage
FROM accesslog_analytics.access_logs
WHERE elb_status_code >= 400
GROUP BY elb_status_code
ORDER BY error_count DESC;
""",
        'hourly_traffic.sql': """
-- 시간별 트래픽 분석
SELECT 
    DATE_TRUNC('hour', from_iso8601_timestamp(time)) as hour,
    COUNT(*) as request_count,
    AVG(request_processing_time + target_processing_time + response_processing_time) as avg_response_time,
    COUNT(CASE WHEN elb_status_code >= 400 THEN 1 END) as error_count
FROM accesslog_analytics.access_logs
GROUP BY DATE_TRUNC('hour', from_iso8601_timestamp(time))
ORDER BY hour;
""",
        'user_agent_analysis.sql': """
-- User Agent 분석
SELECT 
    CASE 
        WHEN user_agent LIKE '%bot%' OR user_agent LIKE '%crawler%' THEN 'Bot/Crawler'
        WHEN user_agent LIKE '%Mobile%' OR user_agent LIKE '%Android%' OR user_agent LIKE '%iPhone%' THEN 'Mobile'
        WHEN user_agent LIKE '%Chrome%' THEN 'Chrome'
        WHEN user_agent LIKE '%Firefox%' THEN 'Firefox'
        WHEN user_agent LIKE '%Safari%' THEN 'Safari'
        ELSE 'Other'
    END as user_agent_category,
    COUNT(*) as request_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage
FROM accesslog_analytics.access_logs
GROUP BY 1
ORDER BY request_count DESC;
"""
    }
    
    for filename, query in queries.items():
        with open(filename, 'w') as f:
            f.write(query)
        print(f"Created query file: {filename}")

def run_sample_query():
    """샘플 쿼리 실행"""
    query = """
    SELECT 
        COUNT(*) as total_requests,
        COUNT(DISTINCT client_ip) as unique_ips,
        AVG(request_processing_time + target_processing_time + response_processing_time) as avg_response_time,
        COUNT(CASE WHEN elb_status_code >= 400 THEN 1 END) as error_count
    FROM accesslog_analytics.access_logs
    LIMIT 10;
    """
    
    response = athena_client.start_query_execution(
        QueryString=query,
        ResultConfiguration={
            'OutputLocation': f's3://{ATHENA_RESULTS_BUCKET}/'
        },
        WorkGroup='primary'
    )
    
    query_execution_id = response['QueryExecutionId']
    print(f"Started query execution: {query_execution_id}")
    
    # 쿼리 완료 대기
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = response['QueryExecution']['Status']['State']
        
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        
        print(f"Query status: {status}")
        time.sleep(2)
    
    if status == 'SUCCEEDED':
        # 결과 조회
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        print("\nQuery Results:")
        for row in results['ResultSet']['Rows']:
            print([col.get('VarCharValue', '') for col in row['Data']])
    else:
        print(f"Query failed with status: {status}")

def main():
    print("=== S3, Glue, Athena 파이프라인 설정 시작 ===")
    
    # 1. txt 파일들을 S3에 업로드
    print("\n1. Uploading txt files to S3...")
    txt_files = upload_txt_files()
    print(f"Uploaded {len(txt_files)} files")
    
    # 2. Glue 데이터베이스 생성
    print("\n2. Creating Glue database...")
    create_glue_database()
    
    # 3. Glue 테이블 생성
    print("\n3. Creating Glue table...")
    create_glue_table()
    
    # 4. 샘플 쿼리 생성
    print("\n4. Creating sample queries...")
    create_sample_queries()
    
    # 5. 샘플 쿼리 실행
    print("\n5. Running sample query...")
    try:
        run_sample_query()
    except Exception as e:
        print(f"Query execution failed: {e}")
    
    print("\n=== 설정 완료 ===")
    print(f"Database: {DATABASE_NAME}")
    print(f"Table: {TABLE_NAME}")
    print(f"S3 Location: s3://{BUCKET_NAME}/raw-data/")
    print(f"Athena Results: s3://{ATHENA_RESULTS_BUCKET}/")

if __name__ == "__main__":
    main()
