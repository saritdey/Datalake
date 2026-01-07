import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any, List
from jsonschema import validate, ValidationError

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

# Define schemas for different data sources
SCHEMAS = {
    "iot_sensor": {
        "type": "object",
        "required": ["device_id", "timestamp", "readings"],
        "properties": {
            "device_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "readings": {
                "type": "object",
                "properties": {
                    "temperature": {"type": "number"},
                    "humidity": {"type": "number"}
                }
            }
        }
    },
    "api_events": {
        "type": "object",
        "required": ["event_type", "user_id", "timestamp"],
        "properties": {
            "event_type": {"type": "string"},
            "user_id": {"type": "string"},
            "timestamp": {"type": "string"}
        }
    }
}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validates data from S3 raw zone and moves valid data to processed zone.
    Triggered by S3 events.
    """
    validation_results = []
    
    for record in event.get('Records', []):
        try:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Read data from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Validate data
            source = data.get('source', 'unknown')
            validation_result = validate_data(data, source)
            
            if validation_result['valid']:
                validation_results.append({
                    'key': key,
                    'status': 'valid',
                    'source': source
                })
            else:
                # Log validation errors
                print(f"Validation failed for {key}: {validation_result['errors']}")
                validation_results.append({
                    'key': key,
                    'status': 'invalid',
                    'errors': validation_result['errors']
                })
                
                # Send alert for invalid data
                send_alert(key, validation_result['errors'])
                
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            validation_results.append({
                'key': key if 'key' in locals() else 'unknown',
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': len(validation_results),
            'results': validation_results
        })
    }


def validate_data(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Validate data against schema."""
    errors = []
    
    # Check required top-level fields
    if 'data' not in data:
        errors.append("Missing 'data' field")
        return {'valid': False, 'errors': errors}
    
    # Validate against schema if available
    if source in SCHEMAS:
        try:
            validate(instance=data['data'], schema=SCHEMAS[source])
        except ValidationError as e:
            errors.append(f"Schema validation failed: {e.message}")
    
    # Additional business rules
    if 'ingestion_timestamp' in data:
        try:
            datetime.fromisoformat(data['ingestion_timestamp'])
        except ValueError:
            errors.append("Invalid timestamp format")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def send_alert(key: str, errors: List[str]) -> None:
    """Send SNS alert for validation failures."""
    if 'ALERT_TOPIC_ARN' in os.environ:
        try:
            sns_client.publish(
                TopicArn=os.environ['ALERT_TOPIC_ARN'],
                Subject='Data Validation Failure',
                Message=f"Validation failed for {key}\nErrors: {json.dumps(errors, indent=2)}"
            )
        except Exception as e:
            print(f"Failed to send alert: {str(e)}")
