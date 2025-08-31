
-- User Agent 분석
SELECT 
    CASE 
        WHEN user_agent LIKE '%bot%' OR user_agent LIKE '%crawler%' THEN 'Bot/Crawler'
        WHEN user_agent LIKE '%Mobile%' OR user_agent LIKE '%Android%' OR user_agent LIKE '%iPhone%' THEN 'Mobile'
        WHEN user_agent LIKE '%Chrome%' THEN 'Chrome'
        WHEN user_agent LIKE '%Firefox%' THEN 'Firefox'
        WHEN user_agent LIKE '%Safari%' THEN 'Safari'
        ELSE 'Other'
    END as user_agent_category,
    COUNT(*) as request_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM accesslog_analytics.access_logs), 2) as percentage
FROM accesslog_analytics.access_logs
GROUP BY 1
ORDER BY request_count DESC;
