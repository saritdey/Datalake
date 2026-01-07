#!/bin/bash

# Data Lake Monitoring Script
# Checks health and status of data lake components

set -e

STACK_NAME="${STACK_NAME:-data-lake}"
REGION="${REGION:-us-east-1}"

echo "========================================="
echo "Data Lake Health Check"
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo "========================================="

# Get stack outputs
echo -e "\n1. Retrieving stack information..."
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].StackStatus' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" == "NOT_FOUND" ]; then
    echo "  ✗ Stack not found: $STACK_NAME"
    exit 1
fi

echo "  Stack Status: $STACK_STATUS"

# Check S3 buckets
echo -e "\n2. Checking S3 buckets..."
RAW_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`RawBucket`].OutputValue' \
  --output text \
  --region "$REGION")

PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`ProcessedBucket`].OutputValue' \
  --output text \
  --region "$REGION")

CURATED_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`CuratedBucket`].OutputValue' \
  --output text \
  --region "$REGION")

# Count objects in each bucket
RAW_COUNT=$(aws s3 ls "s3://$RAW_BUCKET" --recursive --region "$REGION" | wc -l)
PROCESSED_COUNT=$(aws s3 ls "s3://$PROCESSED_BUCKET" --recursive --region "$REGION" | wc -l)
CURATED_COUNT=$(aws s3 ls "s3://$CURATED_BUCKET" --recursive --region "$REGION" | wc -l)

echo "  Raw Bucket: $RAW_BUCKET ($RAW_COUNT objects)"
echo "  Processed Bucket: $PROCESSED_BUCKET ($PROCESSED_COUNT objects)"
echo "  Curated Bucket: $CURATED_BUCKET ($CURATED_COUNT objects)"

# Check Lambda function
echo -e "\n3. Checking Lambda function..."
LAMBDA_NAME="$STACK_NAME-ingestion"
LAMBDA_STATUS=$(aws lambda get-function \
  --function-name "$LAMBDA_NAME" \
  --query 'Configuration.State' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "NOT_FOUND")

echo "  Lambda Status: $LAMBDA_STATUS"

if [ "$LAMBDA_STATUS" == "Active" ]; then
    # Get recent invocations
    INVOCATIONS=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/Lambda \
      --metric-name Invocations \
      --dimensions Name=FunctionName,Value="$LAMBDA_NAME" \
      --start-time "$(date -u -v-1H '+%Y-%m-%dT%H:%M:%S')" \
      --end-time "$(date -u '+%Y-%m-%dT%H:%M:%S')" \
      --period 3600 \
      --statistics Sum \
      --region "$REGION" \
      --query 'Datapoints[0].Sum' \
      --output text 2>/dev/null || echo "0")
    
    ERRORS=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/Lambda \
      --metric-name Errors \
      --dimensions Name=FunctionName,Value="$LAMBDA_NAME" \
      --start-time "$(date -u -v-1H '+%Y-%m-%dT%H:%M:%S')" \
      --end-time "$(date -u '+%Y-%m-%dT%H:%M:%S')" \
      --period 3600 \
      --statistics Sum \
      --region "$REGION" \
      --query 'Datapoints[0].Sum' \
      --output text 2>/dev/null || echo "0")
    
    echo "  Invocations (last hour): $INVOCATIONS"
    echo "  Errors (last hour): $ERRORS"
fi

# Check Glue crawler
echo -e "\n4. Checking Glue crawler..."
CRAWLER_NAME="$STACK_NAME-raw-crawler"
CRAWLER_STATE=$(aws glue get-crawler \
  --name "$CRAWLER_NAME" \
  --query 'Crawler.State' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "NOT_FOUND")

echo "  Crawler State: $CRAWLER_STATE"

# Check Glue database
echo -e "\n5. Checking Glue database..."
DATABASE_NAME="${STACK_NAME}_db"
TABLE_COUNT=$(aws glue get-tables \
  --database-name "$DATABASE_NAME" \
  --region "$REGION" \
  --query 'length(TableList)' \
  --output text 2>/dev/null || echo "0")

echo "  Database: $DATABASE_NAME"
echo "  Tables: $TABLE_COUNT"

# Check API Gateway
echo -e "\n6. Checking API Gateway..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region "$REGION")

echo "  API Endpoint: $API_ENDPOINT"

# Test API health (optional)
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_ENDPOINT" \
      -H "Content-Type: application/json" \
      -d '{"source":"health-check","data":{"test":true}}' 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" == "200" ]; then
        echo "  API Health: ✓ Healthy (HTTP $HTTP_CODE)"
    else
        echo "  API Health: ✗ Unhealthy (HTTP $HTTP_CODE)"
    fi
fi

echo -e "\n========================================="
echo "Health Check Complete"
echo "========================================="
