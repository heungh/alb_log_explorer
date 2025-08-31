
-- 시간별 트래픽 분석
SELECT 
    DATE_TRUNC('hour', from_iso8601_timestamp(time)) as hour,
    COUNT(*) as request_count,
    AVG(request_processing_time + target_processing_time + response_processing_time) as avg_response_time,
    COUNT(CASE WHEN elb_status_code >= 400 THEN 1 END) as error_count
FROM accesslog_analytics.access_logs
GROUP BY DATE_TRUNC('hour', from_iso8601_timestamp(time))
ORDER BY hour;
