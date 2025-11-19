"""
Test script to send 100 create-customer requests and verify metadata
"""
import json
import os
import requests
import time

BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/v1/makerequest"

def send_request(payload):
    """Send a single request"""
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=10)
        return response.status_code, response.json()
    except Exception as e:
        return None, str(e)

def main():
    print("=" * 80)
    print("TESTING 100 CREATE-CUSTOMER REQUESTS")
    print("=" * 80)
    
    # Load all payloads
    payloads_dir = "payloads"
    if not os.path.exists(payloads_dir):
        print(f"Error: {payloads_dir} directory not found")
        print("Run: python generate_payloads.py first")
        return
    
    payload_files = sorted([f for f in os.listdir(payloads_dir) if f.endswith('.json')])
    print(f"\nFound {len(payload_files)} payloads\n")
    
    results = {
        "success": 0,
        "failed": 0,
        "responses": []
    }
    
    # Send all requests
    for i, filename in enumerate(payload_files, 1):
        filepath = os.path.join(payloads_dir, filename)
        
        with open(filepath, 'r') as f:
            payload = json.load(f)
        
        status_code, response = send_request(payload)
        
        if status_code == 200:
            results["success"] += 1
            print(f"[{i:3d}] ✓ {payload['phone']} - {payload['name']}")
        else:
            results["failed"] += 1
            print(f"[{i:3d}] ✗ {payload['phone']} - Error: {status_code}")
        
        results["responses"].append({
            "payload": payload,
            "status": status_code,
            "response": response
        })
        
        # Small delay between requests
        time.sleep(0.1)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Requests: {len(payload_files)}")
    print(f"Successful: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {(results['success']/len(payload_files)*100):.1f}%")
    
    # Check metadata files
    print("\n" + "=" * 80)
    print("CHECKING METADATA FILES")
    print("=" * 80)
    
    business_meta_path = "DataModels/Salon/salon_meta.json"
    customer_meta_path = "data/businesses/salon/customer_metadata.json"
    
    # Check business metadata
    if os.path.exists(business_meta_path):
        with open(business_meta_path, 'r') as f:
            business_meta = json.load(f)
        print(f"\n✓ Business Metadata Found: {business_meta_path}")
        print(f"  Total Customers: {business_meta.get('metadata', {}).get('total_customers', 0)}")
        print(f"  Phone Mappings: {len(business_meta.get('phone_mappings', {}))}")
    else:
        print(f"\n✗ Business Metadata NOT Found: {business_meta_path}")
    
    # Check customer metadata
    if os.path.exists(customer_meta_path):
        with open(customer_meta_path, 'r') as f:
            customer_meta = json.load(f)
        print(f"\n✓ Customer Metadata Found: {customer_meta_path}")
        print(f"  Total Customers in Cache: {len(customer_meta.get('customers', {}))}")
        print(f"  Metadata: {customer_meta.get('metadata', {})}")
    else:
        print(f"\n✗ Customer Metadata NOT Found: {customer_meta_path}")
    
    # Save results
    results_file = "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {results_file}")

if __name__ == "__main__":
    main()
