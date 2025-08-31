
-- 에러 분석
SELECT 
    elb_status_code,
    COUNT(*) as error_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as error_percentage
FROM accesslog_analytics.access_logs
WHERE elb_status_code >= 400
GROUP BY elb_status_code
ORDER BY error_count DESC;
