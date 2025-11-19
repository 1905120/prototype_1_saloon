"""
Generate 100 different create-customer payloads for testing
"""
import json
import os

# Create test directory if it doesn't exist
os.makedirs("payloads", exist_ok=True)

# Generate 100 different payloads
for i in range(1, 101):
    phone = f"98765432{i:02d}"  # 9876543200 to 9876543299
    name = f"Customer {i}"
    
    payload = {
        "action": "create-customer",
        "phone": phone,
        "name": name,
        "business": "salon"
    }
    
    # Save to file
    filename = f"payloads/payload_{i:03d}.json"
    with open(filename, 'w') as f:
        json.dump(payload, f, indent=2)
    
    print(f"Created {filename}")

print(f"\nGenerated 100 payloads in test/payloads/")
