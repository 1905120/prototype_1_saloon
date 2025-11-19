"""
Test script for create customer execution
Tests the complete flow from endpoint to worker completion
"""
import asyncio
import json
from src.core.context import ApplicationContext
from src.checkbusiness import check_and_route_business
from src.business.salon.cache import SharedMetaCache
from src.core.customer_management.shared import SharedCustomerCache


async def test_create_customer():
    """Test create customer flow"""
    
    print("\n" + "="*80)
    print("TEST: Create Customer Execution")
    print("="*80)
    
    # Initialize context
    app_context = ApplicationContext()
    app_context.start_processing()
    
    try:
        # Test payload
        payload = {
            "action": "create-customer",
            "phone": "9876543210",
            "name": "John Doe",
            "business": "salon"
        }
        
        print("\n1. Request Payload:")
        print(json.dumps(payload, indent=2))
        
        # Check salon metadata before
        print("\n2. Salon Metadata Before:")
        salon_meta = SharedMetaCache.get()
        print(f"   Phone mappings: {salon_meta.phone_mappings}")
        
        # Check customer metadata before
        print("\n3. Customer Metadata Before:")
        customer_meta = SharedCustomerCache.get()
        print(f"   Total customers: {customer_meta.metadata.total_customers}")
        print(f"   Entries: {[k for k in customer_meta.__dict__.keys() if k != 'metadata']}")
        
        # Execute request
        print("\n4. Executing Request...")
        response = await check_and_route_business(
            payload,
            None,  # No background tasks needed for test
            app_context
        )
        
        print("\n5. Response:")
        print(json.dumps(response, indent=2, default=str))
        
        # Check salon metadata after
        print("\n6. Salon Metadata After:")
        salon_meta = SharedMetaCache.get()
        print(f"   Phone mappings: {salon_meta.phone_mappings}")
        
        # Check customer metadata after
        print("\n7. Customer Metadata After:")
        customer_meta = SharedCustomerCache.get()
        print(f"   Total customers: {customer_meta.metadata.total_customers}")
        print(f"   Entries: {[k for k in customer_meta.__dict__.keys() if k != 'metadata']}")
        
        # Check customer metadata file
        print("\n8. Customer Metadata File Content:")
        try:
            with open("DataModels/Salon/CustomerSchema/Schema/meta-data.json", 'r') as f:
                meta_file = json.load(f)
            print(json.dumps(meta_file, indent=2))
        except Exception as e:
            print(f"   Error reading file: {e}")
        
        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        app_context.shutdown()


if __name__ == "__main__":
    asyncio.run(test_create_customer())
