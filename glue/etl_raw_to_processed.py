import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import (
    col, from_json, current_timestamp, to_date, 
    year, month, dayofmonth, hash, when, lit
)
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from awsglue.dynamicframe import DynamicFrame

# Get job parameters
args = getResolvedOptions(
    sys.argv, 
    ['JOB_NAME', 'RAW_BUCKET', 'PROCESSED_BUCKET']
)

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Enable job bookmarking for incremental processing
job_bookmark = job.get_bookmark()

print(f"Starting ETL job: {args['JOB_NAME']}")
print(f"Raw bucket: {args['RAW_BUCKET']}")
print(f"Processed bucket: {args['PROCESSED_BUCKET']}")

# Read from raw zone (all sources)
raw_path = f"s3://{args['RAW_BUCKET']}/"
print(f"Reading from: {raw_path}")

try:
    df = spark.read.json(raw_path)
    
    # Data quality checks
    print(f"Initial record count: {df.count()}")
    
    # Filter out null data and invalid records
    df_clean = df.filter(
        col("data").isNotNull() & 
        col("source").isNotNull() &
        col("ingestion_timestamp").isNotNull()
    )
    
    print(f"After null filtering: {df_clean.count()}")
    
    # Add processing metadata
    processed_df = df_clean \
        .withColumn("processing_timestamp", current_timestamp()) \
        .withColumn("record_hash", hash(col("data"))) \
        .dropDuplicates(["ingestion_timestamp", "source", "record_hash"])
    
    print(f"After deduplication: {processed_df.count()}")
    
    # Extract partition columns from ingestion_timestamp
    processed_df = processed_df \
        .withColumn("ingestion_date", to_date(col("ingestion_timestamp"))) \
        .withColumn("year", year(col("ingestion_date"))) \
        .withColumn("month", month(col("ingestion_date"))) \
        .withColumn("day", dayofmonth(col("ingestion_date")))
    
    # Add data quality flags
    processed_df = processed_df \
        .withColumn("quality_score", 
            when(col("metadata").isNotNull(), lit(100))
            .otherwise(lit(80))
        )
    
    # Write to processed zone in Parquet format with partitioning
    processed_path = f"s3://{args['PROCESSED_BUCKET']}/processed/"
    print(f"Writing to: {processed_path}")
    
    processed_df.write \
        .mode("append") \
        .partitionBy("source", "year", "month", "day") \
        .parquet(processed_path)
    
    print("ETL job completed successfully")
    
    # Commit job bookmark
    job.commit()
    
except Exception as e:
    print(f"Error in ETL job: {str(e)}")
    raise
