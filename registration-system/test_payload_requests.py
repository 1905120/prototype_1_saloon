"""
Test script to send 10 requests with sample payload
"""
import requests
import json
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample payload
payload = {
    "phone": "9876543210",
    "business": "salon",
    "name": "John Doe",
    "service_type": "hair-cutting"
}

# API endpoint
url = "http://localhost:8000/api/v1/makerequest"

if __name__ == "__main__":
    logger.info("Starting 10 requests test...")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    for i in range(1, 11):
        try:
            logger.info(f"\n=== Request {i} ===")
            response = requests.post(url, json=payload, timeout=10)
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {response.json()}")
            time.sleep(0.5)  # Small delay between requests
        except requests.exceptions.ConnectionError:
            logger.error(f"Request {i}: Connection error - Server not running")
            break
        except Exception as e:
            logger.error(f"Request {i}: Error - {str(e)}")
    
    logger.info("\n=== All requests completed ===")
