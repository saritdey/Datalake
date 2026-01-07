-- Sample Athena queries for data lake analytics
-- Replace 'data-lake_db' with your actual database name

-- ============================================
-- RAW ZONE QUERIES
-- ============================================

-- Query recent raw data
SELECT 
    source,
    ingestion_timestamp,
    data,
    metadata
FROM "data-lake_db"."raw_data"
WHERE year = '2025' 
    AND month = '11'
    AND day = '25'
LIMIT 10;

-- Count records by source
SELECT 
    source,
    COUNT(*) as record_count,
    MIN(ingestion_timestamp) as first_ingestion,
    MAX(ingestion_timestamp) as last_ingestion
FROM "data-lake_db"."raw_data"
GROUP BY source
ORDER BY record_count DESC;

-- Data ingestion rate by hour
SELECT 
    DATE_TRUNC('hour', CAST(ingestion_timestamp AS TIMESTAMP)) as hour,
    source,
    COUNT(*) as events_per_hour
FROM "data-lake_db"."raw_data"
WHERE year = '2025' AND month = '11'
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- ============================================
-- PROCESSED ZONE QUERIES
-- ============================================

-- Query processed data with quality scores
SELECT 
    source,
    ingestion_timestamp,
    processing_timestamp,
    quality_score,
    data
FROM "data-lake_db"."processed_data"
WHERE year = 2025 
    AND month = 11
    AND day = 25
    AND quality_score >= 80
LIMIT 100;

-- Data quality analysis
SELECT 
    source,
    AVG(quality_score) as avg_quality,
    MIN(quality_score) as min_quality,
    MAX(quality_score) as max_quality,
    COUNT(*) as total_records,
    SUM(CASE WHEN quality_score >= 90 THEN 1 ELSE 0 END) as high_quality_records
FROM "data-lake_db"."processed_data"
WHERE year = 2025 AND month = 11
GROUP BY source
ORDER BY avg_quality DESC;

-- Processing lag analysis
SELECT 
    source,
    AVG(
        DATE_DIFF('second', 
            CAST(ingestion_timestamp AS TIMESTAMP),
            CAST(processing_timestamp AS TIMESTAMP)
        )
    ) as avg_processing_lag_seconds,
    COUNT(*) as record_count
FROM "data-lake_db"."processed_data"
WHERE year = 2025 AND month = 11
GROUP BY source
ORDER BY avg_processing_lag_seconds DESC;

-- ============================================
-- CURATED ZONE QUERIES
-- ============================================

-- Daily summary statistics
SELECT 
    source,
    year,
    month,
    day,
    record_count,
    avg_quality_score,
    first_ingestion,
    last_ingestion
FROM "data-lake_db"."daily_summary"
WHERE year = 2025 AND month = 11
ORDER BY year DESC, month DESC, day DESC, record_count DESC;

-- Source performance overview
SELECT 
    source,
    total_records,
    avg_quality,
    first_seen,
    last_seen,
    DATE_DIFF('day', CAST(first_seen AS DATE), CAST(last_seen AS DATE)) as days_active
FROM "data-lake_db"."source_statistics"
ORDER BY total_records DESC;

-- Hourly trends
SELECT 
    hour_start,
    source,
    events_per_hour,
    avg_quality
FROM "data-lake_db"."hourly_metrics"
WHERE hour_start >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
ORDER BY hour_start DESC, events_per_hour DESC;

-- ============================================
-- ADVANCED ANALYTICS
-- ============================================

-- Week-over-week comparison
WITH weekly_stats AS (
    SELECT 
        source,
        DATE_TRUNC('week', CAST(CONCAT(CAST(year AS VARCHAR), '-', 
            LPAD(CAST(month AS VARCHAR), 2, '0'), '-',
            LPAD(CAST(day AS VARCHAR), 2, '0')) AS DATE)) as week_start,
        SUM(record_count) as weekly_records
    FROM "data-lake_db"."daily_summary"
    GROUP BY source, DATE_TRUNC('week', CAST(CONCAT(CAST(year AS VARCHAR), '-', 
        LPAD(CAST(month AS VARCHAR), 2, '0'), '-',
        LPAD(CAST(day AS VARCHAR), 2, '0')) AS DATE))
)
SELECT 
    source,
    week_start,
    weekly_records,
    LAG(weekly_records, 1) OVER (PARTITION BY source ORDER BY week_start) as prev_week_records,
    ROUND(
        100.0 * (weekly_records - LAG(weekly_records, 1) OVER (PARTITION BY source ORDER BY week_start)) 
        / NULLIF(LAG(weekly_records, 1) OVER (PARTITION BY source ORDER BY week_start), 0),
        2
    ) as percent_change
FROM weekly_stats
ORDER BY source, week_start DESC;

-- Data freshness check
SELECT 
    source,
    MAX(ingestion_timestamp) as last_data_received,
    DATE_DIFF('minute', 
        CAST(MAX(ingestion_timestamp) AS TIMESTAMP),
        CURRENT_TIMESTAMP
    ) as minutes_since_last_data
FROM "data-lake_db"."processed_data"
WHERE year = 2025 AND month = 11
GROUP BY source
HAVING DATE_DIFF('minute', 
    CAST(MAX(ingestion_timestamp) AS TIMESTAMP),
    CURRENT_TIMESTAMP
) > 60
ORDER BY minutes_since_last_data DESC;

-- ============================================
-- COST OPTIMIZATION QUERIES
-- ============================================

-- Partition scan analysis (to optimize queries)
SELECT 
    source,
    year,
    month,
    COUNT(*) as record_count,
    ROUND(SUM(LENGTH(CAST(data AS VARCHAR))) / 1024.0 / 1024.0, 2) as data_size_mb
FROM "data-lake_db"."processed_data"
GROUP BY source, year, month
ORDER BY data_size_mb DESC;

-- Identify duplicate records
SELECT 
    record_hash,
    COUNT(*) as duplicate_count,
    ARRAY_AGG(ingestion_timestamp) as timestamps
FROM "data-lake_db"."processed_data"
WHERE year = 2025 AND month = 11
GROUP BY record_hash
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 100;
