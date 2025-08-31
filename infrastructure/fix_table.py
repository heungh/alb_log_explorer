#!/usr/bin/env python3
import boto3

REGION = 'ap-northeast-2'
DATABASE_NAME = 'alb_analytics'
TABLE_NAME = 'access_logs'
BUCKET_NAME = 'alb-logs-analytics-1756017037'

def recreate_table():
    """올바른 정규식으로 테이블 재생성"""
    glue = boto3.client('glue', region_name=REGION)
    
    # 기존 테이블 삭제
    try:
        glue.delete_table(DatabaseName=DATABASE_NAME, Name=TABLE_NAME)
        print("기존 테이블 삭제됨")
    except:
        print("기존 테이블 없음")
    
    # 새 테이블 생성
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
                {'Name': 'classification_reason', 'Type': 'string'},
                {'Name': 'tid', 'Type': 'string'}
            ],
            'Location': f's3://{BUCKET_NAME}/logs/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.RegexSerDe',
                'Parameters': {
                    'input.regex': '([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]* ([^ ]*) [^ ]*)\" \"([^\"]*)\" ([A-Z0-9-]+) ([A-Za-z0-9.-]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^\"]*)\" ([-.0-9]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^ ]*)\" \"([^\s]+?)\" \"([^\s]+)\" \"([^ ]*)\" \"([^ ]*)\" ([^ ]*)'
                }
            }
        }
    }
    
    glue.create_table(DatabaseName=DATABASE_NAME, TableInput=table_input)
    print("새 테이블 생성 완료")

if __name__ == "__main__":
    recreate_table()
