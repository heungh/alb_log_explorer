
-- 응답 시간 분석
SELECT 
    CASE 
        WHEN response_time1 < 1000 THEN 'Fast (<1s)'
        WHEN response_time1 < 3000 THEN 'Medium (1-3s)'
        WHEN response_time1 < 5000 THEN 'Slow (3-5s)'
        ELSE 'Very Slow (>5s)'
    END as response_category,
    COUNT(*) as request_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage,
    AVG(response_time1) as avg_response_time
FROM accesslog_analytics.access_logs
WHERE response_time1 IS NOT NULL
GROUP BY 1
ORDER BY avg_response_time;
