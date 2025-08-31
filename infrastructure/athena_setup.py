#!/usr/bin/env python3
import boto3
import json

# AWS 클라이언트 초기화
region = 'ap-northeast-2'
athena_client = boto3.client('athena', region_name=region)

WORKGROUP_NAME = 'accesslog-analytics'
ATHENA_RESULTS_BUCKET = f'aws-athena-query-results-{region}-181136804328'

def create_athena_workgroup():
    """Athena 워크그룹 생성"""
    try:
        athena_client.create_work_group(
            Name=WORKGROUP_NAME,
            Description='Workgroup for access log analytics',
            Configuration={
                'ResultConfiguration': {
                    'OutputLocation': f's3://{ATHENA_RESULTS_BUCKET}/accesslog-analytics/'
                },
                'EnforceWorkGroupConfiguration': True,
                'PublishCloudWatchMetricsEnabled': True
            }
        )
        print(f"Created Athena workgroup: {WORKGROUP_NAME}")
    except athena_client.exceptions.InvalidRequestException as e:
        if "already exists" in str(e):
            print(f"Workgroup {WORKGROUP_NAME} already exists")
        else:
            raise e

def run_queries():
    """생성된 쿼리 파일들을 실행"""
    import os
    import time
    
    query_files = [f for f in os.listdir('.') if f.endswith('.sql')]
    
    for query_file in query_files:
        print(f"\nExecuting {query_file}...")
        
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
            # 결과 조회 (처음 5행만)
            results = athena_client.get_query_results(
                QueryExecutionId=query_execution_id,
                MaxResults=5
            )
            
            print("Results (first 5 rows):")
            for i, row in enumerate(results['ResultSet']['Rows']):
                if i == 0:  # 헤더
                    headers = [col.get('VarCharValue', '') for col in row['Data']]
                    print(f"  {' | '.join(headers)}")
                    print(f"  {'-' * (len(' | '.join(headers)))}")
                else:
                    values = [col.get('VarCharValue', '') for col in row['Data']]
                    print(f"  {' | '.join(values)}")

def main():
    print("=== Athena 추가 설정 ===")
    
    # 1. Athena 워크그룹 생성
    print("\n1. Creating Athena workgroup...")
    create_athena_workgroup()
    
    # 2. 쿼리 실행
    print("\n2. Running sample queries...")
    run_queries()
    
    print(f"\n=== 설정 완료 ===")
    print(f"Workgroup: {WORKGROUP_NAME}")
    print(f"Results Location: s3://{ATHENA_RESULTS_BUCKET}/accesslog-analytics/")
    print("\nAthena 콘솔에서 다음 정보로 접속하세요:")
    print(f"- Region: {region}")
    print(f"- Database: accesslog_analytics")
    print(f"- Workgroup: {WORKGROUP_NAME}")

if __name__ == "__main__":
    main()
