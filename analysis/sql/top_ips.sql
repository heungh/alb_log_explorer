
-- 상위 클라이언트 IP 분석
SELECT 
    client_ip,
    COUNT(*) as request_count,
    AVG(request_processing_time + target_processing_time + response_processing_time) as avg_response_time,
    SUM(received_bytes + sent_bytes) as total_bytes
FROM accesslog_analytics.access_logs
WHERE elb_status_code < 400
GROUP BY client_ip
ORDER BY request_count DESC
LIMIT 20;
