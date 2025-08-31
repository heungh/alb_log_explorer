
-- 요청 분석
SELECT 
    regexp_extract(request, '"(GET|POST|PUT|DELETE)', 1) as http_method,
    COUNT(*) as request_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage
FROM accesslog_analytics.access_logs
WHERE request LIKE '"%'
GROUP BY regexp_extract(request, '"(GET|POST|PUT|DELETE)', 1)
ORDER BY request_count DESC;
