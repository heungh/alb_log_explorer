#!/usr/bin/env python3
import boto3
import json

def check_ec2_ip(target_ip, region='ap-northeast-2'):
    """EC2 인스턴스에서 특정 IP 사용 여부 확인"""
    ec2 = boto3.client('ec2', region_name=region)
    
    # 모든 EC2 인스턴스 조회
    response = ec2.describe_instances()
    
    matches = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            
            # Private IP 확인
            if instance.get('PrivateIpAddress') == target_ip:
                matches.append({
                    'type': 'EC2_PRIVATE',
                    'instance_id': instance_id,
                    'ip': target_ip,
                    'state': instance['State']['Name']
                })
            
            # Public IP 확인
            if instance.get('PublicIpAddress') == target_ip:
                matches.append({
                    'type': 'EC2_PUBLIC',
                    'instance_id': instance_id,
                    'ip': target_ip,
                    'state': instance['State']['Name']
                })
            
            # ENI 추가 IP 확인
            for eni in instance.get('NetworkInterfaces', []):
                for private_ip in eni.get('PrivateIpAddresses', []):
                    if private_ip.get('PrivateIpAddress') == target_ip:
                        matches.append({
                            'type': 'EC2_ENI',
                            'instance_id': instance_id,
                            'eni_id': eni['NetworkInterfaceId'],
                            'ip': target_ip,
                            'state': instance['State']['Name']
                        })
    
    return matches

def check_eks_ip(target_ip, cluster_name, region='ap-northeast-2'):
    """EKS Pod에서 특정 IP 사용 여부 확인"""
    import subprocess
    
    try:
        # kubectl을 통한 Pod IP 확인
        cmd = f"kubectl get pods -A -o wide --field-selector=status.podIP={target_ip}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')[1:]  # 헤더 제외
            matches = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    matches.append({
                        'type': 'EKS_POD',
                        'namespace': parts[0],
                        'pod_name': parts[1],
                        'ip': parts[5],
                        'node': parts[6] if len(parts) > 6 else 'unknown'
                    })
            return matches
    except Exception as e:
        print(f"EKS 확인 중 오류: {e}")
    
    return []

def check_cloudtrail_logs(target_ip, hours=24):
    """CloudTrail에서 IP 사용 기록 확인"""
    logs = boto3.client('logs')
    
    query = f"""
    fields @timestamp, sourceIPAddress, eventName, userIdentity.type
    | filter sourceIPAddress = "{target_ip}"
    | sort @timestamp desc
    | limit 100
    """
    
    try:
        response = logs.start_query(
            logGroupName='/aws/cloudtrail',
            startTime=int((datetime.now() - timedelta(hours=hours)).timestamp()),
            endTime=int(datetime.now().timestamp()),
            queryString=query
        )
        return response['queryId']
    except Exception as e:
        print(f"CloudTrail 조회 실패: {e}")
        return None

if __name__ == "__main__":
    target_ip = input("확인할 IP 주소: ")
    
    print(f"\n🔍 IP {target_ip} 사용 여부 확인 중...\n")
    
    # EC2 확인
    ec2_matches = check_ec2_ip(target_ip)
    if ec2_matches:
        print("✅ EC2에서 발견:")
        for match in ec2_matches:
            print(f"  - {match['type']}: {match['instance_id']} ({match['state']})")
    
    # EKS 확인 (클러스터명 입력 필요)
    cluster_name = input("\nEKS 클러스터명 (선택사항): ")
    if cluster_name:
        eks_matches = check_eks_ip(target_ip, cluster_name)
        if eks_matches:
            print("✅ EKS Pod에서 발견:")
            for match in eks_matches:
                print(f"  - Pod: {match['namespace']}/{match['pod_name']} on {match['node']}")
    
    if not ec2_matches and not eks_matches:
        print("❌ 해당 IP를 사용하는 리소스를 찾을 수 없습니다.")
