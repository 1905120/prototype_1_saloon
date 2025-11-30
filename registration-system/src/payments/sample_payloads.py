"""Sample payloads for testing payment endpoints"""

# Sample payload for creating a UPI payment
CREATE_UPI_PAYMENT_SAMPLE = {
    "business_name": "My Salon",
    "customer_id": "CUST_9876543210",
    "merchant_upi": "mysalon@upi",
    "merchant_name": "My Salon",
    "amount": 500.00,
    "description": "Payment for haircut service",
    "metadata": {
        "service_id": "SRV_001",
        "service_name": "Haircut",
        "booking_id": "BK_12345",
        "appointment_date": "2024-11-25",
        "appointment_time": "14:30"
    }
}

# Sample payload for verifying payment
VERIFY_PAYMENT_SAMPLE = {
    "business_name": "My Salon",
    "transaction_id": "TXN123ABC456DEF",
    "payment_status": "SUCCESS",
    "reference_id": "BANK_REF_20241125_001"
}

# Sample payload for failed payment verification
VERIFY_PAYMENT_FAILED_SAMPLE = {
    "business_name": "My Salon",
    "transaction_id": "TXN123ABC456DEF",
    "payment_status": "FAILED",
    "reference_id": None
}

# Sample payload for pending payment verification
VERIFY_PAYMENT_PENDING_SAMPLE = {
    "business_name": "My Salon",
    "transaction_id": "TXN123ABC456DEF",
    "payment_status": "PENDING",
    "reference_id": None
}


# Example curl commands for testing
CURL_EXAMPLES = """
# 1. Create UPI Payment
curl -X POST http://localhost:8000/api/v1/payments/create-upi-payment \\
  -H "Content-Type: application/json" \\
  -d '{
    "business_name": "My Salon",
    "customer_id": "CUST_9876543210",
    "merchant_upi": "mysalon@upi",
    "merchant_name": "My Salon",
    "amount": 500.00,
    "description": "Payment for haircut service",
    "metadata": {
      "service_id": "SRV_001",
      "service_name": "Haircut",
      "booking_id": "BK_12345"
    }
  }'

# 2. Verify Payment (Success)
curl -X POST http://localhost:8000/api/v1/payments/verify-payment \\
  -H "Content-Type: application/json" \\
  -d '{
    "business_name": "My Salon",
    "transaction_id": "TXN123ABC456DEF",
    "payment_status": "SUCCESS",
    "reference_id": "BANK_REF_20241125_001"
  }'

# 3. Get Payment Status
curl -X GET http://localhost:8000/api/v1/payments/status/My%20Salon/TXN123ABC456DEF

# 4. Get Customer Payments
curl -X GET http://localhost:8000/api/v1/payments/customer/My%20Salon/CUST_9876543210
"""


# Python requests examples
PYTHON_EXAMPLES = """
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/payments"

# 1. Create UPI Payment
def create_payment():
    payload = {
        "business_name": "My Salon",
        "customer_id": "CUST_9876543210",
        "merchant_upi": "mysalon@upi",
        "merchant_name": "My Salon",
        "amount": 500.00,
        "description": "Payment for haircut service",
        "metadata": {
            "service_id": "SRV_001",
            "service_name": "Haircut",
            "booking_id": "BK_12345"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/create-upi-payment",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))
    
    return response.json()

# 2. Verify Payment
def verify_payment(transaction_id):
    payload = {
        "business_name": "My Salon",
        "transaction_id": transaction_id,
        "payment_status": "SUCCESS",
        "reference_id": "BANK_REF_20241125_001"
    }
    
    response = requests.post(
        f"{BASE_URL}/verify-payment",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))
    
    return response.json()

# 3. Get Payment Status
def get_status(business_name, transaction_id):
    response = requests.get(
        f"{BASE_URL}/status/{business_name}/{transaction_id}"
    )
    
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))
    
    return response.json()

# 4. Get Customer Payments
def get_customer_payments(business_name, customer_id):
    response = requests.get(
        f"{BASE_URL}/customer/{business_name}/{customer_id}"
    )
    
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))
    
    return response.json()

# Usage
if __name__ == "__main__":
    # Create payment
    result = create_payment()
    transaction_id = result['result']['transaction_id']
    
    # Verify payment
    verify_payment(transaction_id)
    
    # Get status
    get_status("My Salon", transaction_id)
    
    # Get customer payments
    get_customer_payments("My Salon", "CUST_9876543210")
"""
