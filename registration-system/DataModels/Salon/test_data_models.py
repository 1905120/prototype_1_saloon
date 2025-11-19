import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_models import GetFieldMapping

def test_get_field_mapping():
    """Test the GetFieldMapping function for all classes"""
    
    print("=" * 60)
    print("Testing GetFieldMapping Function")
    print("=" * 60)
    
    # Test Customer
    print("\n1. Testing Customer class:")
    try:
        customer_mapping = GetFieldMapping('Customer')
        print(f"   Success! Found {len(customer_mapping)} fields")
        for field_num in sorted(customer_mapping.keys()):
            print(f"   {field_num}: {customer_mapping[field_num]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Client
    print("\n2. Testing Client class:")
    try:
        client_mapping = GetFieldMapping('Client')
        print(f"   Success! Found {len(client_mapping)} fields")
        for field_num in sorted(client_mapping.keys()):
            print(f"   {field_num}: {client_mapping[field_num]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Appointment
    print("\n3. Testing Appointment class:")
    try:
        appointment_mapping = GetFieldMapping('Appointment')
        print(f"   Success! Found {len(appointment_mapping)} fields")
        for field_num in sorted(appointment_mapping.keys()):
            print(f"   {field_num}: {appointment_mapping[field_num]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test BookingConfirmation
    print("\n4. Testing BookingConfirmation class:")
    try:
        booking_mapping = GetFieldMapping('BookingConfirmation')
        print(f"   Success! Found {len(booking_mapping)} fields")
        for field_num in sorted(booking_mapping.keys()):
            print(f"   {field_num}: {booking_mapping[field_num]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test invalid class
    print("\n5. Testing invalid class:")
    try:
        invalid_mapping = GetFieldMapping('InvalidClass')
        print(f"   Unexpected success!")
    except ValueError as e:
        print(f"   Expected error caught: {e}")
    except Exception as e:
        print(f"   Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_get_field_mapping()
