#!/usr/bin/env python3
"""
ALB Log Explorer 데모 버전 - 실제 로그 파일 사용
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
        """실제 로그 파일 파싱"""
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
    
    def generate_user_agent(self, index):
        """가상의 User-Agent 생성"""
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
            'Googlebot/2.1 (+http://www.google.com/bot.html)',
            'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)'
        ]
        return agents[index % len(agents)]

# 로그 파서 초기화
log_parser = LogParser('./data/140.248.29.3-logs-fieldfiltered.txt')

@app.route('/')
def index():
    return render_template('demo.html')

@app.route('/api/search', methods=['POST'])
def search():
    """로그 검색 API"""
    data = request.get_json()
    
    filters = data.get('filters', {})
    time_range = data.get('time_range', {})
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
    
    # 시간 범위 필터 (간단 구현)
    if time_range.get('start') or time_range.get('end'):
        # 실제 구현에서는 datetime 파싱 필요
        pass
    
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
