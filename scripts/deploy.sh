#!/bin/bash

set -e

# IMPORTANT: Change STACK_NAME to something unique for your organization
# S3 bucket names must be globally unique across all AWS accounts
STACK_NAME="${STACK_NAME:-data-lake-${USER}-$(date +%s)}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
REGION="${REGION:-us-east-1}"

echo "========================================="
echo "Deploying Data Lake Infrastructure"
echo "Stack: $STACK_NAME"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "========================================="

# Deploy CloudFormation stack
echo "Step 1: Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file cloudformation/data-lake.yaml \
  --stack-name "$STACK_NAME" \
  --parameter-overrides Environment="$ENVIRONMENT" \
  --capabilities CAPABILITY_IAM \
  --region "$REGION"

# Get stack outputs
echo "Step 2: Retrieving stack outputs..."
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

API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region "$REGION")

echo "Raw Bucket: $RAW_BUCKET"
echo "Processed Bucket: $PROCESSED_BUCKET"
echo "API Endpoint: $API_ENDPOINT"

# Upload Glue scripts to S3
echo "Step 3: Uploading Glue ETL scripts..."
aws s3 cp glue/etl_raw_to_processed.py "s3://$PROCESSED_BUCKET/scripts/" --region "$REGION"
aws s3 cp glue/etl_processed_to_curated.py "s3://$PROCESSED_BUCKET/scripts/" --region "$REGION"

echo "========================================="
echo "Deployment completed successfully!"
echo "========================================="
echo ""
echo "Stack Outputs:"
echo "  API Endpoint: $API_ENDPOINT"
echo "  Raw Bucket: $RAW_BUCKET"
echo "  Processed Bucket: $PROCESSED_BUCKET"
echo ""
echo "Next steps:"
echo "1. Test the API endpoint"
echo "2. Run: python scripts/test_ingestion.py"
echo "3. Check CloudWatch dashboard"
echo ""
echo "Test ingestion:"
echo "curl -X POST $API_ENDPOINT \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"source\": \"test-system\", \"data\": {\"key\": \"value\"}}'"
