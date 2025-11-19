"""
Write live/current data to storage
"""
import json
import os
from typing import Dict, Any


class WriteLive:
    """Handles writing live data to storage"""
    
    CUSTOMER_LIVE_PATH = "src/data/stored_data/customer/live"
    CLIENT_LIVE_PATH = "src/data/stored_data/client/live"
    
    @staticmethod
    def _ensure_directory_exists(path: str) -> None:
        """Create directory if it doesn't exist"""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def write_customer(customer_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write customer record to live storage
        
        Args:
            customer_record: Customer data to write
        
        Returns:
            Response with status and file path
        """
        WriteLive._ensure_directory_exists(WriteLive.CUSTOMER_LIVE_PATH)
        
        # Use phone as filename for easy lookup
        phone = customer_record.get("phone")
        filename = f"{phone}.json"
        filepath = os.path.join(WriteLive.CUSTOMER_LIVE_PATH, filename)
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(customer_record, f, indent=2)
        
        return {
            "status": "SUCCESS",
            "message": "Customer record written to live storage",
            "filepath": filepath,
            "customerId": customer_record.get("customerId")
        }
    
    @staticmethod
    def write_client(client_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write client record to live storage
        
        Args:
            client_record: Client data to write
        
        Returns:
            Response with status and file path
        """
        WriteLive._ensure_directory_exists(WriteLive.CLIENT_LIVE_PATH)
        
        # Use mobile as filename for easy lookup
        mobile = client_record.get("mobile")
        filename = f"{mobile}.json"
        filepath = os.path.join(WriteLive.CLIENT_LIVE_PATH, filename)
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(client_record, f, indent=2)
        
        return {
            "status": "SUCCESS",
            "message": "Client record written to live storage",
            "filepath": filepath,
            "clientId": client_record.get("clientId")
        }
