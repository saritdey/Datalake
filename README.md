# AWS Data Lake

Enterprise-grade, API-driven data lake architecture for real-time analytics using AWS serverless services.

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Data Sources│────▶│ API Gateway  │────▶│   Lambda    │────▶│  S3 Raw Zone │
│ (IoT/Apps)  │     │              │     │  Ingestion  │     │              │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                      │
                    ┌──────────────┐     ┌─────────────┐            │
                    │  QuickSight  │◀────│   Athena    │◀───────────┤
                    │  Dashboard   │     │   Queries   │            │
                    └──────────────┘     └──────┬──────┘            │
                                                 │                   │
                    ┌──────────────┐     ┌──────▼──────┐     ┌──────▼───────┐
                    │S3 Curated    │◀────│ Glue ETL    │◀────│S3 Processed  │
                    │     Zone     │     │    Jobs     │     │     Zone     │
                    └──────────────┘     └─────────────┘     └──────────────┘
                                                 ▲
                    ┌──────────────┐     ┌──────┴──────┐
                    │ EventBridge  │────▶│    Step     │
                    │  Scheduler   │     │  Functions  │
                    └──────────────┘     └─────────────┘
```

## Components

### Data Ingestion Layer
- **API Gateway**: HTTP REST API endpoint for real-time data ingestion
- **Lambda (Ingestion)**: Validates and stores incoming data with partitioning
- **Lambda (Validation)**: Schema validation and data quality checks

### Storage Layer (S3)
- **Raw Zone**: Immutable landing zone for all incoming data (JSON format)
- **Processed Zone**: Cleaned, deduplicated data in Parquet format
- **Curated Zone**: Business-ready aggregated datasets

### Processing Layer
- **AWS Glue Crawler**: Automatic schema discovery and catalog updates
- **AWS Glue ETL Jobs**: 
  - Raw → Processed: Data cleaning, deduplication, format conversion
  - Processed → Curated: Business logic, aggregations, denormalization
- **Step Functions**: Orchestrates complex ETL workflows

### Analytics Layer
- **Glue Data Catalog**: Centralized metadata repository
- **Amazon Athena**: Serverless SQL query engine
- **QuickSight**: Business intelligence and visualization (optional)

### Orchestration & Monitoring
- **EventBridge**: Scheduled ETL job triggers
- **CloudWatch**: Logs, metrics, and dashboards
- **SNS**: Alerting for failures and anomalies

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.11+
- Bash shell (for deployment scripts)
- curl (for testing)

## Quick Start

### 1. Deploy Infrastructure

```bash
# Set environment variables (optional)
export STACK_NAME="my-data-lake"
export ENVIRONMENT="dev"
export REGION="us-east-1"

# Deploy CloudFormation stack
./scripts/deploy.sh
```

The deployment script will:
- Create all AWS resources via CloudFormation
- Upload Glue ETL scripts to S3
- Output the API endpoint and bucket names

### 2. Test Data Ingestion

```bash
# Get API endpoint from stack outputs
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Run comprehensive test suite
python scripts/test_ingestion.py $API_ENDPOINT
```

### 3. Monitor Health

```bash
# Check system health
./scripts/monitor.sh
```

## Usage Examples

### Ingest Data via API

```bash
# Single record ingestion
curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{
    "source": "iot_sensors",
    "data": {
      "device_id": "sensor_001",
      "temperature": 22.5,
      "humidity": 65,
      "timestamp": "2025-11-25T10:00:00Z"
    },
    "metadata": {
      "location": "warehouse_a",
      "firmware_version": "2.1.0"
    }
  }'
```

### Query Data with Athena

```sql
-- Query raw data
SELECT * FROM "data-lake_db"."raw_data"
WHERE source = 'iot_sensors'
  AND year = '2025'
  AND month = '11'
LIMIT 10;

-- Analyze processed data
SELECT 
    source,
    COUNT(*) as record_count,
    AVG(quality_score) as avg_quality
FROM "data-lake_db"."processed_data"
WHERE year = 2025 AND month = 11
GROUP BY source;
```

See `athena/sample_queries.sql` for more examples.

### Run ETL Jobs Manually

```bash
# Start Glue crawler
aws glue start-crawler --name $STACK_NAME-raw-crawler

# Run ETL job
aws glue start-job-run --job-name $STACK_NAME-etl-raw-to-processed

# Execute Step Functions workflow
aws stepfunctions start-execution \
  --state-machine-arn <state-machine-arn> \
  --input '{}'
```

## Data Flow

1. **Ingestion**: External systems POST data to API Gateway
2. **Landing**: Lambda writes raw JSON to S3 raw zone with partitioning
3. **Cataloging**: Glue Crawler discovers schemas and updates catalog
4. **Processing**: Glue ETL job transforms raw → processed (Parquet)
5. **Curation**: Second ETL job creates aggregated business views
6. **Analytics**: Users query via Athena or visualize in QuickSight

## Partitioning Strategy

Data is partitioned for optimal query performance:

```
Raw Zone:     s3://bucket/source/year=YYYY/month=MM/day=DD/timestamp.json
Processed:    s3://bucket/processed/source=X/year=YYYY/month=MM/day=DD/*.parquet
Curated:      s3://bucket/curated/dataset_name/source=X/year=YYYY/month=MM/*.parquet
```

## Monitoring & Alerts

### CloudWatch Dashboard
Access the dashboard: AWS Console → CloudWatch → Dashboards → `{stack-name}-monitoring`

Metrics tracked:
- Lambda invocations and errors
- API Gateway request count and latency
- S3 storage metrics
- Glue job success/failure rates

### Alerts
SNS topic: `{stack-name}-alerts`

Configured alarms:
- Lambda error rate > 5 in 5 minutes
- Glue job failures
- API Gateway 5xx errors

Subscribe to alerts:
```bash
aws sns subscribe \
  --topic-arn <alert-topic-arn> \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## Cost Optimization

- **S3 Lifecycle**: Raw data transitions to IA after 90 days
- **Athena**: Use partitioning to reduce data scanned
- **Glue**: Job bookmarking for incremental processing
- **Lambda**: Right-sized memory allocation

Estimated monthly cost (low volume):
- S3: $5-20
- Lambda: $1-5
- Glue: $10-30
- Athena: Pay per query ($5/TB scanned)
- API Gateway: $3.50/million requests

## Security

- **Encryption**: S3 server-side encryption enabled
- **IAM**: Least privilege roles for all services
- **API**: Can be secured with API keys or IAM auth
- **VPC**: Can be deployed in VPC for private access
- **Audit**: CloudTrail logs all API calls

## Troubleshooting

### Lambda Errors
```bash
# View recent logs
aws logs tail /aws/lambda/$STACK_NAME-ingestion --follow
```

### Glue Job Failures
```bash
# Get job run details
aws glue get-job-runs --job-name $STACK_NAME-etl-raw-to-processed --max-results 5
```

### No Data in Athena
1. Check if data exists in S3 raw zone
2. Run Glue crawler to update catalog
3. Verify table partitions: `MSCK REPAIR TABLE table_name;`

## Project Structure

```
.
├── athena/
│   └── sample_queries.sql          # Example Athena queries
├── cloudformation/
│   └── data-lake.yaml              # Infrastructure as Code
├── glue/
│   ├── etl_raw_to_processed.py     # Raw → Processed ETL
│   └── etl_processed_to_curated.py # Processed → Curated ETL
├── lambda/
│   ├── ingestion/                  # Data ingestion function
│   └── validation/                 # Data validation function
├── scripts/
│   ├── deploy.sh                   # Deployment automation
│   ├── test_ingestion.py           # Integration tests
│   └── monitor.sh                  # Health check script
├── README.md                       # This file
└── STORIES.md                      # User stories and estimates
```

## Development Roadmap

See `STORIES.md` for detailed user stories and effort estimates.

**Total Estimated Effort**: 394-538 hours across 8 epics

Key milestones:
1. ✅ Infrastructure Setup (24-32 hours)
2. ✅ Data Ingestion (40-56 hours)
3. ⏳ Data Cataloging (24-32 hours)
4. ⏳ Data Processing (56-72 hours)
5. ⏳ Analytics & Querying (40-56 hours)
6. ⏳ Monitoring & Operations (48-64 hours)
7. ⏳ Security & Compliance (56-72 hours)
8. ⏳ Documentation & Training (106-154 hours)

## Contributing

1. Follow AWS best practices
2. Test changes in dev environment first
3. Update documentation for any changes
4. Use meaningful commit messages

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check troubleshooting section
2. Review CloudWatch logs
3. Consult AWS documentation
4. Open an issue in the repository
