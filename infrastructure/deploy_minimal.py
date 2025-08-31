#!/usr/bin/env python3
import boto3
import json
import os
import time

# AWS 설정
REGION = 'ap-northeast-2'
BUCKET_NAME = 'alb-logs-analytics-' + str(int(time.time()))
DATABASE_NAME = 'alb_analytics'
TABLE_NAME = 'access_logs'

def create_s3_bucket():
    """S3 버킷 생성"""
    s3 = boto3.client('s3', region_name=REGION)
    
    s3.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={'LocationConstraint': REGION}
    )
    print(f"Created S3 bucket: {BUCKET_NAME}")
    
    # 로그 파일 업로드
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
    for file in txt_files:
        s3.upload_file(file, BUCKET_NAME, f'logs/{file}')
        print(f"Uploaded {file}")

def create_glue_resources():
    """Glue 데이터베이스 및 테이블 생성"""
    glue = boto3.client('glue', region_name=REGION)
    
    # 데이터베이스 생성
    try:
        glue.create_database(
            DatabaseInput={
                'Name': DATABASE_NAME,
                'Description': 'ALB Access Log Analytics'
            }
        )
        print(f"Created database: {DATABASE_NAME}")
    except:
        print(f"Database {DATABASE_NAME} already exists")
    
    # 테이블 생성
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
                {'Name': 'user_agent', 'Type': 'string'}
            ],
            'Location': f's3://{BUCKET_NAME}/logs/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.RegexSerDe',
                'Parameters': {
                    'input.regex': '([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]* [^ ]* [^ ]*)\" \"([^\"]*)\""'
                }
            }
        }
    }
    
    try:
        glue.create_table(DatabaseName=DATABASE_NAME, TableInput=table_input)
        print(f"Created table: {TABLE_NAME}")
    except:
        print(f"Table {TABLE_NAME} already exists")

def create_athena_workgroup():
    """Athena 워크그룹 생성"""
    athena = boto3.client('athena', region_name=REGION)
    
    try:
        athena.create_work_group(
            Name='alb-analytics',
            Configuration={
                'ResultConfiguration': {
                    'OutputLocation': f's3://{BUCKET_NAME}/athena-results/'
                }
            }
        )
        print("Created Athena workgroup: alb-analytics")
    except:
        print("Workgroup already exists")

def test_query():
    """테스트 쿼리 실행"""
    athena = boto3.client('athena', region_name=REGION)
    
    query = f"""
    SELECT 
        client_ip,
        COUNT(*) as requests,
        AVG(request_processing_time) as avg_time
    FROM {DATABASE_NAME}.{TABLE_NAME}
    GROUP BY client_ip
    ORDER BY requests DESC
    LIMIT 10
    """
    
    response = athena.start_query_execution(
        QueryString=query,
        ResultConfiguration={
            'OutputLocation': f's3://{BUCKET_NAME}/athena-results/'
        },
        WorkGroup='alb-analytics'
    )
    
    print(f"Test query started: {response['QueryExecutionId']}")

def main():
    print("=== ALB Access Log 분석 솔루션 배포 시작 ===")
    
    create_s3_bucket()
    create_glue_resources()
    create_athena_workgroup()
    test_query()
    
    print("\n=== 배포 완료 ===")
    print(f"S3 Bucket: {BUCKET_NAME}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Table: {TABLE_NAME}")
    print(f"Region: {REGION}")

if __name__ == "__main__":
    main()
