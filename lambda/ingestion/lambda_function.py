import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any

s3_client = boto3.client('s3')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for data ingestion via API Gateway.
    
    Expected payload:
    {
        "source": "system_name",
        "data": {...},
        "metadata": {...}  # optional
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if 'source' not in body or 'data' not in body:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required fields: source and data'
                })
            }
        
        source = body['source']
        data = body['data']
        metadata = body.get('metadata', {})
        
        # Generate S3 key with partitioning
        timestamp = datetime.utcnow()
        key = generate_s3_key(source, timestamp)
        
        # Prepare data object
        data_object = {
            'ingestion_timestamp': timestamp.isoformat(),
            'source': source,
            'metadata': metadata,
            'data': data
        }
        
        # Write to S3 raw zone
        s3_client.put_object(
            Bucket=os.environ['RAW_BUCKET'],
            Key=key,
            Body=json.dumps(data_object, indent=2),
            ContentType='application/json',
            Metadata={
                'source': source,
                'ingestion-timestamp': timestamp.isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Data ingested successfully',
                'key': key,
                'bucket': os.environ['RAW_BUCKET'],
                'timestamp': timestamp.isoformat()
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def generate_s3_key(source: str, timestamp: datetime) -> str:
    """
    Generate partitioned S3 key for data organization.
    Format: source/year=YYYY/month=MM/day=DD/timestamp.json
    """
    return (
        f"{source}/"
        f"year={timestamp.year}/"
        f"month={timestamp.month:02d}/"
        f"day={timestamp.day:02d}/"
        f"{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
    )
