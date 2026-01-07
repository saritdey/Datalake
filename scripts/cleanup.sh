#!/bin/bash

# Cleanup script to delete all data lake resources
# WARNING: This will delete all data and cannot be undone!

set -e

STACK_NAME="${STACK_NAME:-data-lake}"
REGION="${REGION:-us-east-1}"

echo "========================================="
echo "⚠️  DATA LAKE CLEANUP WARNING ⚠️"
echo "========================================="
echo "This will DELETE:"
echo "  - CloudFormation stack: $STACK_NAME"
echo "  - All S3 buckets and data"
echo "  - Lambda functions"
echo "  - Glue catalog and jobs"
echo "  - All other resources"
echo ""
read -p "Are you sure? Type 'DELETE' to confirm: " CONFIRM

if [ "$CONFIRM" != "DELETE" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."

# Get bucket names before deleting stack
echo "Step 1: Retrieving bucket names..."
RAW_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`RawBucket`].OutputValue' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "")

PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`ProcessedBucket`].OutputValue' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "")

CURATED_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`CuratedBucket`].OutputValue' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "")

# Empty S3 buckets (required before deletion)
if [ -n "$RAW_BUCKET" ]; then
    echo "Step 2: Emptying raw bucket: $RAW_BUCKET"
    aws s3 rm "s3://$RAW_BUCKET" --recursive --region "$REGION" 2>/dev/null || true
fi

if [ -n "$PROCESSED_BUCKET" ]; then
    echo "Step 3: Emptying processed bucket: $PROCESSED_BUCKET"
    aws s3 rm "s3://$PROCESSED_BUCKET" --recursive --region "$REGION" 2>/dev/null || true
fi

if [ -n "$CURATED_BUCKET" ]; then
    echo "Step 4: Emptying curated bucket: $CURATED_BUCKET"
    aws s3 rm "s3://$CURATED_BUCKET" --recursive --region "$REGION" 2>/dev/null || true
fi

# Delete CloudFormation stack
echo "Step 5: Deleting CloudFormation stack..."
aws cloudformation delete-stack \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

echo "Step 6: Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

echo ""
echo "========================================="
echo "✓ Cleanup completed successfully"
echo "========================================="
echo "All resources have been deleted."
