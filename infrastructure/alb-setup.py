import boto3
import json

def setup_alb_logging():
    """ALB 로깅 설정"""
    s3 = boto3.client('s3')
    elbv2 = boto3.client('elbv2')
    
    # S3 버킷 생성
    bucket_name = 'alb-logs-analysis-bucket'
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-2'}
    )
    
    # ALB 로그 활성화
    elbv2.modify_load_balancer_attributes(
        LoadBalancerArn='your-alb-arn',
        Attributes=[
            {'Key': 'access_logs.s3.enabled', 'Value': 'true'},
            {'Key': 'access_logs.s3.bucket', 'Value': bucket_name},
            {'Key': 'access_logs.s3.prefix', 'Value': 'alb-logs'}
        ]
    )

def setup_glue_catalog():
    """Glue 데이터 카탈로그 설정"""
    glue = boto3.client('glue')
    
    glue.create_database(
        DatabaseInput={'Name': 'alb_analytics'}
    )
    
    # ALB 로그 테이블 생성
    table_input = {
        'Name': 'access_logs',
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
                {'Name': 'ssl_protocol', 'Type': 'string'}
            ],
            'Location': 's3://alb-logs-analysis-bucket/alb-logs/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.RegexSerDe',
                'Parameters': {
                    'input.regex': '([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]*) ([^ ]*) (- |[^ ]*)\" \"([^\"]*)\" ([A-Z0-9-]+) ([A-Za-z0-9.-]*)'
                }
            }
        }
    }
    
    glue.create_table(
        DatabaseName='alb_analytics',
        TableInput=table_input
    )
