#!/bin/bash

echo "🚀 ALB Log Explorer 데모 시작"
echo "📊 가상 데모 데이터 (demo-ecommerce.example.com) 사용"

# Flask와 CORS 설치
pip3 install flask flask-cors

# 데모 애플리케이션 실행
echo "🌐 웹 인터페이스: http://localhost:5000"
python3 demo_app.py
