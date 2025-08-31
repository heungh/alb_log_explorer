#!/usr/bin/env python3
import boto3
from datetime import datetime, timedelta

def query_vpc_flow_logs(target_ip, hours=24):
    """VPC Flow Logs에서 특정 IP 추적"""
    logs = boto3.client('logs')
    
    # 소스 IP로 사용된 경우
    source_query = f"""
    fields @timestamp, srcaddr, dstaddr, srcport, dstport, protocol, action
    | filter srcaddr = "{target_ip}"
    | sort @timestamp desc
    | limit 50
    """
    
    # 대상 IP로 사용된 경우  
    dest_query = f"""
    fields @timestamp, srcaddr, dstaddr, srcport, dstport, protocol, action
    | filter dstaddr = "{target_ip}"
    | sort @timestamp desc
    | limit 50
    """
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    try:
        # 소스 IP 쿼리
        source_response = logs.start_query(
            logGroupName='/aws/vpc/flowlogs',
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=source_query
        )
        
        # 대상 IP 쿼리
        dest_response = logs.start_query(
            logGroupName='/aws/vpc/flowlogs',
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=dest_query
        )
        
        return {
            'source_query_id': source_response['queryId'],
            'dest_query_id': dest_response['queryId']
        }
        
    except Exception as e:
        print(f"VPC Flow Logs 쿼리 실패: {e}")
        return None

def get_query_results(query_id):
    """CloudWatch Logs 쿼리 결과 조회"""
    logs = boto3.client('logs')
    
    import time
    while True:
        response = logs.get_query_results(queryId=query_id)
        if response['status'] == 'Complete':
            return response['results']
        elif response['status'] == 'Failed':
            return None
        time.sleep(2)

if __name__ == "__main__":
    target_ip = input("추적할 IP: ")
    
    print(f"VPC Flow Logs에서 {target_ip} 추적 중...")
    
    query_ids = query_vpc_flow_logs(target_ip)
    if query_ids:
        print("쿼리 실행 중... (결과는 CloudWatch Logs Insights에서 확인)")
        print(f"소스 IP 쿼리 ID: {query_ids['source_query_id']}")
        print(f"대상 IP 쿼리 ID: {query_ids['dest_query_id']}")
