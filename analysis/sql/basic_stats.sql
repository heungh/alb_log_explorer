
-- 기본 통계
SELECT 
    COUNT(*) as total_requests,
    COUNT(DISTINCT regexp_extract(client_ip_port, '^([^:]+)', 1)) as unique_ips,
    AVG(response_time1) as avg_response_time1,
    AVG(response_time2) as avg_response_time2
FROM accesslog_analytics.access_logs;
