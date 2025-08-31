# ALB Log Explorer 프로젝트

AWS Application Load Balancer (ALB) 액세스 로그를 분석하고 시각화하는 종합 프로젝트입니다.

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ALB Access    │    │   Log Explorer   │    │   Web Browser   │
│     Logs        │───▶│     Demo App     │───▶│   Dashboard     │
│  (Text Files)   │    │   (Flask API)    │    │   (HTML/JS)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Log Parser     │
                       │   & Analytics    │
                       └──────────────────┘
```

## 📁 프로젝트 구조

```
kidari_analyze_accesslog/
├── alb_demo/                    # 🎯 핵심 데모 애플리케이션
│   ├── demo_app.py             # Flask 메인 애플리케이션
│   ├── run_demo.sh             # 실행 스크립트
│   ├── templates/
│   │   └── demo.html           # 웹 인터페이스
│   └── data/
│       └── demo-logs-final.txt     # 가상 데모 데이터 (개인정보 제거)
├── analysis/                    # 📊 분석 도구
│   ├── scripts/                # Python 분석 스크립트
│   ├── sql/                    # SQL 쿼리 모음
│   └── reports/                # 분석 보고서
├── infrastructure/             # 🏗️ 인프라 설정
├── docs/                       # 📋 문서
├── log_explorer/               # 🔍 다른 로그 탐색기
├── web/                        # 🌐 웹 관련 파일
├── lambda/                     # ⚡ Lambda 함수
└── README.md                   # 이 파일
```

## 🚀 빠른 시작 (데모 실행)

### 1. 사전 요구사항

```bash
# Python 3.7+ 필요
python3 --version

# pip 업그레이드
pip3 install --upgrade pip
```

### 2. 데모 실행

```bash
# 프로젝트 디렉토리로 이동
cd alb_demo

# 실행 스크립트 사용
chmod +x run_demo.sh
./run_demo.sh

# 또는 직접 실행
python3 demo_app.py
```

### 3. 웹 인터페이스 접속

브라우저에서 접속:
```
http://localhost:5000
```

## 💻 핵심 데모 소스코드

### alb_demo/demo_app.py

```python
#!/usr/bin/env python3
"""
ALB Log Explorer 데모 - 가상 데이터 사용
"""
import json
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class LogParser:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.logs = []
        self.parse_logs()
    
    def parse_logs(self):
        """가상 로그 파일 파싱"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 1000:  # 데모용으로 1000개만
                        break
                    
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        client_info = parts[0]
                        received_bytes = parts[1]
                        sent_bytes = parts[2]
                        request = parts[3]
                        
                        # IP 추출
                        client_ip = client_info.split(':')[0]
                        
                        # HTTP 메서드와 URL 추출
                        method_match = re.match(r'"(\w+)\s+([^"]+)"', request)
                        if method_match:
                            method = method_match.group(1)
                            url = method_match.group(2)
                        else:
                            method = 'GET'
                            url = request
                        
                        # 가상의 시간 생성 (최근 24시간 내)
                        fake_time = datetime.now() - timedelta(minutes=i)
                        
                        # 가상의 상태 코드 생성
                        status_code = 200
                        if 'error' in url.lower() or i % 50 == 0:
                            status_code = 404
                        elif i % 100 == 0:
                            status_code = 500
                        
                        log_entry = {
                            'time': fake_time.isoformat(),
                            'client_ip': client_ip,
                            'client_port': client_info.split(':')[1] if ':' in client_info else '80',
                            'elb_status_code': status_code,
                            'request': request.strip('"'),
                            'method': method,
                            'url': url,
                            'user_agent': self.generate_user_agent(i),
                            'received_bytes': int(received_bytes),
                            'sent_bytes': int(sent_bytes),
                            'request_processing_time': round(0.001 + (i % 10) * 0.01, 3),
                            'target_processing_time': round(0.005 + (i % 5) * 0.02, 3),
                            'response_processing_time': round(0.001 + (i % 3) * 0.005, 3)
                        }
                        
                        self.logs.append(log_entry)
        except Exception as e:
            print(f"로그 파싱 오류: {e}")

# 로그 파서 초기화 (가상 데이터 사용)
log_parser = LogParser('./data/demo-logs-final.txt')

@app.route('/')
def index():
    return render_template('demo.html')

@app.route('/api/search', methods=['POST'])
def search():
    """로그 검색 API"""
    data = request.get_json()
    
    filters = data.get('filters', {})
    limit = data.get('limit', 100)
    
    results = log_parser.logs.copy()
    
    # 필터 적용
    if filters.get('client_ip'):
        results = [log for log in results if filters['client_ip'] in log['client_ip']]
    
    if filters.get('status_code'):
        status = int(filters['status_code'])
        results = [log for log in results if log['elb_status_code'] == status]
    
    if filters.get('method'):
        results = [log for log in results if log['method'] == filters['method']]
    
    if filters.get('search_text'):
        search_text = filters['search_text'].lower()
        results = [log for log in results if 
                  search_text in log['request'].lower() or 
                  search_text in log['user_agent'].lower()]
    
    # 결과 제한
    results = results[:limit]
    
    return jsonify({
        'data': results,
        'total': len(results)
    })

@app.route('/api/stats')
def get_stats():
    """기본 통계"""
    logs = log_parser.logs
    
    total_requests = len(logs)
    unique_ips = len(set(log['client_ip'] for log in logs))
    error_count = len([log for log in logs if log['elb_status_code'] >= 400])
    avg_response_time = sum(
        log['request_processing_time'] + 
        log['target_processing_time'] + 
        log['response_processing_time'] 
        for log in logs
    ) / total_requests if total_requests > 0 else 0
    
    return jsonify({
        'data': [{
            'total_requests': total_requests,
            'unique_ips': unique_ips,
            'avg_response_time': round(avg_response_time, 3),
            'error_count': error_count
        }]
    })

if __name__ == '__main__':
    print(f"📊 로그 데이터 로드 완료: {len(log_parser.logs)}개 엔트리")
    print("🚀 데모 서버 시작: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### alb_demo/run_demo.sh

```bash
#!/bin/bash

echo "🚀 ALB Log Explorer 데모 시작"
echo "📊 가상 데모 데이터 (demo-ecommerce.example.com) 사용"

# Flask와 CORS 설치
pip3 install flask flask-cors

# 데모 애플리케이션 실행
echo "🌐 웹 인터페이스: http://localhost:5000"
python3 demo_app.py
```

### 정리된 데모 로그 예시:
```
192.168.1.100:16169	3711	1195	"GET https://demo-ecommerce.example.com:443/api/shop-api-v2/contents/price/PROD_abc123/7?type=RENTAL HTTP/2.0"
192.168.1.100:16169	3160	3244	"GET https://demo-ecommerce.example.com:443/_next/static/chunks/71712.77ab9d1d048c1dcc.js HTTP/2.0"
192.168.1.100:16169	3242	6071	"GET https://demo-ecommerce.example.com:443/images/popup/illust-purchase.png HTTP/2.0"
```

## 🎯 사용 방법

### 1. 기본 대시보드

웹 인터페이스에서 확인 가능한 정보:
- **총 요청 수**: 로드된 로그 엔트리 수
- **고유 IP 수**: 접속한 클라이언트 IP 개수
- **평균 응답시간**: 전체 요청의 평균 처리 시간
- **에러 수**: 4xx, 5xx 상태코드 요청 수

### 2. 로그 검색 및 필터링

- **IP 주소 필터링**: 특정 IP 주소로 필터링
- **HTTP 상태코드 필터링**: 200, 404, 500 등으로 필터링
- **HTTP 메서드 필터링**: GET, POST, PUT 등으로 필터링
- **텍스트 검색**: URL이나 User-Agent에서 텍스트 검색

### 3. API 엔드포인트

#### 로그 검색 API
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "client_ip": "192.168.1.100",
      "status_code": "200",
      "method": "GET"
    },
    "limit": 50
  }'
```

#### 통계 API
```bash
curl http://localhost:5000/api/stats
```

## 📊 추가 분석 도구

### analysis/scripts/ - Python 분석 스크립트
- `anomaly_analysis.py` - 이상 패턴 분석
- `security_analysis.py` - 보안 분석
- `ip_detailed_analysis.py` - IP 상세 분석
- `check_ip_usage.py` - IP 사용량 체크

### analysis/sql/ - SQL 쿼리 모음
- `top_ips.sql` - 상위 IP 조회
- `response_time_analysis.sql` - 응답시간 분석
- `user_agent_analysis.sql` - User-Agent 분석
- `error_analysis.sql` - 에러 분석

### analysis/reports/ - 분석 보고서
- `ALB_Log_Analysis_Report.md` - 로그 분석 보고서
- `ALB_Security_Analysis_Report.html` - 보안 분석 보고서
- `Detailed_Technical_Analysis.md` - 기술적 상세 분석

## 🏗️ 인프라 설정

### infrastructure/ - AWS 인프라 설정
- `setup_analytics_pipeline.py` - 분석 파이프라인 설정
- `athena_setup.py` - Athena 설정
- `deploy.py` - 배포 스크립트

## 🔧 커스터마이징

### 로그 파일 경로 변경
```python
# alb_demo/demo_app.py에서
log_parser = LogParser('./data/your-log-file.txt')
```

### 포트 변경
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

### 로그 엔트리 수 제한 변경
```python
if i >= 10000:  # 10000개로 증가
    break
```

## 🐛 문제 해결

### 1. 포트 충돌
```bash
# 다른 포트 사용
python3 demo_app.py --port 8080
```

### 2. 로그 파일 없음
```bash
# 데이터 파일 확인
ls -la alb_demo/data/
```

### 3. 의존성 오류
```bash
# 가상환경 사용
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors
```

## 📈 확장 가능성

- **실시간 로그 스트리밍**: AWS Kinesis 연동
- **데이터베이스 연동**: Athena, ElasticSearch 연동
- **알림 시스템**: 임계값 기반 알림
- **고급 시각화**: Chart.js 차트 추가

## 📝 라이선스

이 프로젝트는 데모 및 학습 목적으로 제작되었습니다.

---

**🚀 데모 실행: `cd alb_demo && ./run_demo.sh` 후 http://localhost:5000 접속**
