
-- 상위 클라이언트 IP 분석 (업데이트됨)
SELECT 
    regexp_extract(client_ip_port, '^([^:]+)', 1) as client_ip,
    COUNT(*) as request_count,
    AVG(response_time1) as avg_response_time1,
    AVG(response_time2) as avg_response_time2
FROM accesslog_analytics.access_logs
GROUP BY regexp_extract(client_ip_port, '^([^:]+)', 1)
ORDER BY request_count DESC
LIMIT 20;
