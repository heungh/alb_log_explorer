import boto3
import json
import zipfile
import os

def deploy_solution():
    """전체 솔루션 배포"""
    
    # 1. Lambda 함수 배포
    deploy_lambda_function()
    
    # 2. API Gateway 설정
    setup_api_gateway()
    
    # 3. S3에 웹사이트 배포
    deploy_website()
    
    print("배포 완료!")

def deploy_lambda_function():
    """Lambda 함수 배포"""
    lambda_client = boto3.client('lambda')
    
    # Lambda 패키지 생성
    with zipfile.ZipFile('lambda_function.zip', 'w') as zip_file:
        zip_file.write('lambda/natural_language_search.py', 'lambda_function.py')
    
    with open('lambda_function.zip', 'rb') as zip_file:
        lambda_client.create_function(
            FunctionName='alb-log-search',
            Runtime='python3.9',
            Role='arn:aws:iam::account:role/lambda-execution-role',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_file.read()},
            Timeout=30
        )

def setup_api_gateway():
    """API Gateway 설정"""
    apigateway = boto3.client('apigateway')
    
    # REST API 생성
    api = apigateway.create_rest_api(
        name='alb-log-search-api',
        description='ALB Log Natural Language Search API'
    )
    
    api_id = api['id']
    
    # 리소스 및 메서드 생성
    resources = apigateway.get_resources(restApiId=api_id)
    root_id = resources['items'][0]['id']
    
    resource = apigateway.create_resource(
        restApiId=api_id,
        parentId=root_id,
        pathPart='search'
    )
    
    apigateway.put_method(
        restApiId=api_id,
        resourceId=resource['id'],
        httpMethod='POST',
        authorizationType='NONE'
    )
    
    # Lambda 통합 설정
    lambda_arn = f"arn:aws:lambda:ap-northeast-2:account:function:alb-log-search"
    
    apigateway.put_integration(
        restApiId=api_id,
        resourceId=resource['id'],
        httpMethod='POST',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=f"arn:aws:apigateway:ap-northeast-2:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    )
    
    # 배포
    apigateway.create_deployment(
        restApiId=api_id,
        stageName='prod'
    )

def deploy_website():
    """웹사이트 S3 배포"""
    s3 = boto3.client('s3')
    
    bucket_name = 'alb-log-search-website'
    
    # 버킷 생성
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-2'}
    )
    
    # 웹사이트 설정
    s3.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration={
            'IndexDocument': {'Suffix': 'index.html'}
        }
    )
    
    # HTML 파일 업로드
    s3.upload_file('web/index.html', bucket_name, 'index.html')

if __name__ == "__main__":
    deploy_solution()
