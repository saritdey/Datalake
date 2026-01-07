#!/usr/bin/env python3

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

def test_single_ingestion(api_endpoint: str) -> bool:
    """Test single record ingestion"""
    
    test_payload = {
        "source": "test-system",
        "data": {
            "user_id": "12345",
            "event": "page_view",
            "timestamp": datetime.utcnow().isoformat(),
            "properties": {
                "page": "/home",
                "referrer": "google.com"
            }
        },
        "metadata": {
            "version": "1.0",
            "environment": "test"
        }
    }
    
    print(f"\n{'='*60}")
    print("Test 1: Single Record Ingestion")
    print(f"{'='*60}")
    print(f"Endpoint: {api_endpoint}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            api_endpoint,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✓ Single ingestion successful!")
            return True
        else:
            print("\n✗ Single ingestion failed!")
            return False
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


def test_batch_ingestion(api_endpoint: str) -> bool:
    """Test batch record ingestion"""
    
    print(f"\n{'='*60}")
    print("Test 2: Batch Ingestion (Multiple Records)")
    print(f"{'='*60}")
    
    success_count = 0
    total_records = 5
    
    for i in range(total_records):
        payload = {
            "source": f"iot_sensor_{i % 3}",
            "data": {
                "device_id": f"device_{i:03d}",
                "timestamp": datetime.utcnow().isoformat(),
                "readings": {
                    "temperature": 20 + i,
                    "humidity": 50 + i * 2
                }
            },
            "metadata": {
                "batch_id": "test_batch_001",
                "record_number": i
            }
        }
        
        try:
            response = requests.post(
                api_endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"  ✓ Record {i+1}/{total_records} ingested")
            else:
                print(f"  ✗ Record {i+1}/{total_records} failed: {response.status_code}")
            
            time.sleep(0.5)  # Small delay between requests
            
        except Exception as e:
            print(f"  ✗ Record {i+1}/{total_records} error: {str(e)}")
    
    print(f"\nBatch Results: {success_count}/{total_records} successful")
    return success_count == total_records


def test_validation(api_endpoint: str) -> bool:
    """Test data validation (should fail)"""
    
    print(f"\n{'='*60}")
    print("Test 3: Validation (Invalid Payload)")
    print(f"{'='*60}")
    
    invalid_payload = {
        "data": {"some": "data"}
        # Missing required 'source' field
    }
    
    print(f"Payload: {json.dumps(invalid_payload, indent=2)}")
    
    try:
        response = requests.post(
            api_endpoint,
            json=invalid_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("\n✓ Validation working correctly (rejected invalid data)")
            return True
        else:
            print("\n✗ Validation failed (should have rejected invalid data)")
            return False
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


def test_different_sources(api_endpoint: str) -> bool:
    """Test ingestion from different sources"""
    
    print(f"\n{'='*60}")
    print("Test 4: Multiple Data Sources")
    print(f"{'='*60}")
    
    sources = [
        {
            "source": "web_analytics",
            "data": {
                "session_id": "sess_123",
                "page_views": 5,
                "duration": 120
            }
        },
        {
            "source": "mobile_app",
            "data": {
                "app_version": "2.1.0",
                "user_action": "button_click",
                "screen": "home"
            }
        },
        {
            "source": "api_logs",
            "data": {
                "endpoint": "/api/users",
                "method": "GET",
                "status_code": 200,
                "response_time_ms": 45
            }
        }
    ]
    
    success_count = 0
    for source_data in sources:
        try:
            response = requests.post(
                api_endpoint,
                json=source_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"  ✓ Source '{source_data['source']}' ingested")
            else:
                print(f"  ✗ Source '{source_data['source']}' failed")
            
            time.sleep(0.3)
        except Exception as e:
            print(f"  ✗ Source '{source_data['source']}' error: {str(e)}")
    
    print(f"\nMulti-source Results: {success_count}/{len(sources)} successful")
    return success_count == len(sources)


def run_all_tests(api_endpoint: str):
    """Run all test scenarios"""
    
    print(f"\n{'#'*60}")
    print("# DATA LAKE INGESTION TEST SUITE")
    print(f"{'#'*60}")
    print(f"Target: {api_endpoint}")
    print(f"Time: {datetime.utcnow().isoformat()}")
    
    results = {
        "Single Ingestion": test_single_ingestion(api_endpoint),
        "Batch Ingestion": test_batch_ingestion(api_endpoint),
        "Validation": test_validation(api_endpoint),
        "Multiple Sources": test_different_sources(api_endpoint)
    }
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ingestion.py <api_endpoint>")
        print("\nExample:")
        print("  python test_ingestion.py https://abc123.execute-api.us-east-1.amazonaws.com/dev/ingest")
        sys.exit(1)
    
    exit_code = run_all_tests(sys.argv[1])
    sys.exit(exit_code)
