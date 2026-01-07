import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import (
    col, explode, struct, count, avg, sum as spark_sum,
    min as spark_min, max as spark_max, window, to_timestamp
)

# Get job parameters
args = getResolvedOptions(
    sys.argv,
    ['JOB_NAME', 'PROCESSED_BUCKET', 'CURATED_BUCKET', 'DATABASE_NAME']
)

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

print(f"Starting curated ETL job: {args['JOB_NAME']}")

# Read from processed zone
processed_path = f"s3://{args['PROCESSED_BUCKET']}/processed/"
df = spark.read.parquet(processed_path)

print(f"Processing {df.count()} records")

# Create aggregated views for analytics

# 1. Daily summary by source
daily_summary = df.groupBy("source", "year", "month", "day") \
    .agg(
        count("*").alias("record_count"),
        avg("quality_score").alias("avg_quality_score"),
        spark_min("ingestion_timestamp").alias("first_ingestion"),
        spark_max("ingestion_timestamp").alias("last_ingestion")
    )

curated_daily_path = f"s3://{args['CURATED_BUCKET']}/daily_summary/"
daily_summary.write \
    .mode("overwrite") \
    .partitionBy("source", "year", "month") \
    .parquet(curated_daily_path)

print(f"Daily summary written to: {curated_daily_path}")

# 2. Source statistics
source_stats = df.groupBy("source") \
    .agg(
        count("*").alias("total_records"),
        avg("quality_score").alias("avg_quality"),
        spark_min("ingestion_timestamp").alias("first_seen"),
        spark_max("ingestion_timestamp").alias("last_seen")
    )

curated_stats_path = f"s3://{args['CURATED_BUCKET']}/source_statistics/"
source_stats.write \
    .mode("overwrite") \
    .parquet(curated_stats_path)

print(f"Source statistics written to: {curated_stats_path}")

# 3. Time-series data (hourly aggregations)
df_with_hour = df.withColumn(
    "hour_timestamp",
    to_timestamp(col("ingestion_timestamp"))
)

hourly_metrics = df_with_hour.groupBy(
    window(col("hour_timestamp"), "1 hour"),
    "source"
).agg(
    count("*").alias("events_per_hour"),
    avg("quality_score").alias("avg_quality")
).select(
    col("window.start").alias("hour_start"),
    col("window.end").alias("hour_end"),
    "source",
    "events_per_hour",
    "avg_quality"
)

curated_hourly_path = f"s3://{args['CURATED_BUCKET']}/hourly_metrics/"
hourly_metrics.write \
    .mode("overwrite") \
    .partitionBy("source") \
    .parquet(curated_hourly_path)

print(f"Hourly metrics written to: {curated_hourly_path}")

print("Curated ETL job completed successfully")
job.commit()
