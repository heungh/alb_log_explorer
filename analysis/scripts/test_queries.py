#!/usr/bin/env python3
import boto3
import time
import os

# AWS 클라이언트 초기화
region = 'ap-northeast-2'
athena_client = boto3.client('athena', region_name=region)

WORKGROUP_NAME = 'accesslog-analytics'
ATHENA_RESULTS_BUCKET = f'aws-athena-query-results-{region}-181136804328'

def run_query(query_file):
    """쿼리 파일 실행"""
    print(f"\n=== Executing {query_file} ===")
    
    with open(query_file, 'r') as f:
        query = f.read()
    
    response = athena_client.start_query_execution(
        QueryString=query,
        ResultConfiguration={
            'OutputLocation': f's3://{ATHENA_RESULTS_BUCKET}/accesslog-analytics/'
        },
        WorkGroup=WORKGROUP_NAME
    )
    
    query_execution_id = response['QueryExecutionId']
    print(f"Query execution ID: {query_execution_id}")
    
    # 쿼리 완료 대기
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = response['QueryExecution']['Status']['State']
        
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        
        time.sleep(1)
    
    print(f"Query status: {status}")
    
    if status == 'SUCCEEDED':
        # 결과 조회
        results = athena_client.get_query_results(
            QueryExecutionId=query_execution_id,
            MaxResults=10
        )
        
        print("Results:")
        for i, row in enumerate(results['ResultSet']['Rows']):
            if i == 0:  # 헤더
                headers = [col.get('VarCharValue', '') for col in row['Data']]
                print(f"  {' | '.join(headers)}")
                print(f"  {'-' * (len(' | '.join(headers)) + 10)}")
            else:
                values = [col.get('VarCharValue', '') for col in row['Data']]
                print(f"  {' | '.join(values)}")
    else:
        print(f"Query failed: {status}")
        if 'StateChangeReason' in response['QueryExecution']['Status']:
            print(f"Reason: {response['QueryExecution']['Status']['StateChangeReason']}")

def main():
    print("=== 업데이트된 쿼리 테스트 ===")
    
    # 업데이트된 쿼리 파일들 실행
    query_files = [
        'basic_stats.sql',
        'top_ips_updated.sql',
        'request_analysis.sql',
        'response_time_analysis.sql'
    ]
    
    for query_file in query_files:
        if os.path.exists(query_file):
            run_query(query_file)
        else:
            print(f"Query file {query_file} not found")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    main()
