"""
Customer business logic for salon operations
"""
from typing import Dict, Any, List
import logging
import json
from typing import Dict, Any, Optional
from src.common.constants import TEST
import copy
from pydantic import BaseModel
import os

logger = logging.getLogger(__name__)


def validate_against_schema(schema_path: str, data: Dict[str, Any]) -> List[str]:
    """
    Validate a dictionary against a schema loaded from a JSON file and return missing required fields.
    
    Args:
        schema_path: Path to the JSON schema file
        data: Dictionary to validate
    
    Returns:
        List of missing required field names, or empty list if all required fields present
    """
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
    except Exception as e:
        logger.error(f"Error loading schema from {schema_path}: {str(e)}")
        raise
    
    required_fields = schema.get('required', [])
    missing_fields = []
    
    for field in required_fields:
        if hasattr(data, field) or getattr(data, field, None) == None:
            missing_fields.append(field)
    
    return missing_fields, schema


def create_dict_structure(schema: str, data: Dict, action) -> Dict[str, Any]:
    """
    Create a dictionary structure based on schema properties loaded from a JSON file.
    
    Args:
        schema_path: Path to the JSON schema file
    
    Returns:
        Dictionary with keys from schema properties initialized to None
    """
    # try:
    #     with open(schema_path, 'r') as f:
    #         schema = json.load(f)
    # except Exception as e:
    #     logger.error(f"Error loading schema from {schema_path}: {str(e)}")
    #     raise

    properties = schema.get('properties', {})
    structure = {}

    for field_name in properties.keys():
        structure[field_name] = None

    data = clean_payload(structure, data, action)

    return data

class MakeRequestPayloadForUpdateCust(BaseModel):
    action: Optional[str]
    updatedFields: Dict

class MakeRequestPayloadForCreateCust(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dateOfBirth: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    version: Optional[str] = None
    action: Optional[str] = None
    updatedFields: Optional[Dict[str, Any]] = None
    approvalStatus: Optional[str] = None
    updatedAt: Optional[str] = None
    registeredAt: Optional[str] = None
    business: Optional[str] = None

def clean_payload(structure, request_data, action):
    
    data = request_data.model_dump()

    for field in data:
        delattr(request_data, field)

    for each_field in data:
        structure[each_field] = data[each_field]

    # if action == "create-customer":
    #     MakeRequestPayloadForCreateCust(**structure)
    # elif action == "update-customer":
    #     MakeRequestPayloadForUpdateCust(**structure)

    # for each_field in structure:
    #     if each_field in data:
    #         structure[each_field] = data[each_field]
    
    for key, value in structure.items():
        setattr(request_data, key, value)
    
    return request_data

def validate_and_load_payload(action: str, data: Dict):

    from src.common.constants import B_SALON_CUST_CREATE_SCHEM_PATH, B_SALON_CUST_UPDATE_SCHEM_PATH, TEST
    if action == "create-customer" or action == "create":
        schema_path = B_SALON_CUST_CREATE_SCHEM_PATH
    elif action == "update-customer" or action == "update":
        schema_path = B_SALON_CUST_UPDATE_SCHEM_PATH

    missing_fields, schema = validate_against_schema(schema_path, data)

    if not TEST and missing_fields:
        raise Exception("Refer schema - {}. Invalid payload passed for action {}!!!".format(schema_path, action))
    
    data = create_dict_structure(schema, data, action)

    return data

class Customer:
    """Customer business logic handler"""

    def write_record(self, path, data):
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)

            return True
        except :
            return False
    def delete_record(self, path):
        
        os.remove(path)

        return True

    async def create(self, session_cache, current_version_data, field_validation_error) -> Dict[str, Any]:
        """Create new customer"""
        try:

            if hasattr(session_cache, 'session_id') :
                session_id = session_cache.session_id
            else :
                raise Exception("Session Id Missing")
            from src.common.constants import REQUIRED_MAND_FIELD_FOR_SALON_CUSTOMER
            field_validation_error["missing_keys"] = [key for key in field_validation_error["missing_keys"] if key in REQUIRED_MAND_FIELD_FOR_SALON_CUSTOMER]
            if field_validation_error["missing_keys"]:
                missing_fields = [f'missing field :- {each_field}' for each_field in field_validation_error["missing_keys"]]
                raise Exception("; ".join(missing_fields))

            from src.common.constants import SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH, SALON_BUSINESS_CUSTOMER_HISTORY_DATA_PATH

            # Atomic write
            current_record_path     = f"{SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH}/{session_cache.entity_id}.json"
            # old_current_record_path = f"{SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH}/{session_cache.latest_version_record_id}.json"
            # latest_reacord_path     = f"{SALON_BUSINESS_CUSTOMER_HISTORY_DATA_PATH}/{session_cache.latest_version_record_id}.json"
            # raise Exception("Test Error")
            self.write_record(current_record_path, current_version_data)
            # if os.path.exists(old_current_record_path):
            #     self.delete_record(old_current_record_path)
            #     self.write_record(latest_reacord_path, latest_version_data)
            
            # Initialize customer booking map if not exists
            from src.common.constants import SALON_BUSINESS_CUSTOMER_BOOKING_MAP_PATH, SALON_BUSINESS_CUSTOMER_BOOKING_MAP_SCHEMA_PATH
            customer_id = getattr(session_cache, "phone", None)
            booking_map_path = f"{SALON_BUSINESS_CUSTOMER_BOOKING_MAP_PATH}/{customer_id}.json"
            
            if not os.path.exists(booking_map_path):
                # Read schema
                try:
                    with open(SALON_BUSINESS_CUSTOMER_BOOKING_MAP_SCHEMA_PATH, 'r') as f:
                        schema = json.load(f)
                except Exception as schema_err:
                    logger.error(f"Error loading booking map schema: {str(schema_err)}")
                    raise Exception(f"Failed to load booking map schema: {str(schema_err)}")
                
                # Create empty structure based on schema properties
                empty_booking_map = {}
                properties = schema.get('properties', {})
                for prop_name in properties.keys():
                    if prop_name == 'success_bookings' or prop_name == 'failed_cancelled_book':
                        empty_booking_map[prop_name] = 0
                    elif prop_name == 'booking':
                        empty_booking_map[prop_name] = {}
                
                # Write empty booking map
                self.write_record(booking_map_path, empty_booking_map)
                
            return {
                        "result"  : {
                                        "response" : {
                                            "session_id"                : getattr(session_cache, "session_id", None),
                                            "customer_id"               : getattr(session_cache, "phone", None),
                                            "session_record_id"         : getattr(session_cache, "entity_id", None),
                                            "isRecordStored"            : True,
                                            "latest_customer_location"  : getattr(session_cache, "location", None)
                                                    },
                                            "status": "SUCCESS",
                                            "message": "action {0} successfully".format(getattr(session_cache, "action", None))
                                    },
                     "err_details" : {}
                    }
        except Exception as e:
                return {"result"  : {
                                    "response" : {
                                                    "session_id"                : getattr(session_cache, "session_id", None),
                                                    "customer_id"               : getattr(session_cache, "phone", None),
                                                    "session_record_id"         : getattr(session_cache, "entity_id", None),
                                                    "isRecordStored"            : False,
                                                    "latest_customer_location"  : getattr(session_cache, "location", None)
                                                },
                                    "status"  : "FAILED",
                                    "message" : "action {0} failed due to err {1}".format(getattr(session_cache, "action", None), str(e))
                                    },
                    "err_details" : {
                                        "err_msg" : str(e),
                                        "err_type": "BUSSINESS-PROCESS-ERR"
                                    }
                    }
    
    async def update(self, session_cache, latest_version_record, current_version_data):
        """Update existing customer"""
        try:
            session_id = session_cache.session_id if hasattr(session_cache, 'session_id') else None
            
            # logger.info(f"Updating customer with entity_id: {entity_id}, seq_id: {seq_id}")
            
            # customer_key = payload.phone
            # if customer_key not in cache_data:
            #     return {
            #         "status": "FAILED",
            #         "error": f"Customer not found: {customer_key}",
            #         "message": "Customer does not exist"
            #     }
            
            # customer = cache_data[customer_key]
            # customer.update(payload.updates or {})
            # customer["updated_at"] = __import__('datetime').datetime.now().isoformat()
            # customer["seq_id"] = seq_id
            # raise Exception("Err in customer update")
            return {
                "result": {
                    "response": {
                        "session_id": session_id,
                        "business": session_cache.business,
                        "cust_id": session_cache.entity_id,
                        "service_id": session_cache.operation_id,
                        "isRecordStored": True
                    },
                    "status": "SUCCESS",
                    "message": "Customer updated successfully"
                },
                "err_details": {}
            }
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            return {
                "result": {
                    "response": {
                        "session_id": session_cache.session_id if hasattr(session_cache, 'session_id') else None,
                        "isRecordStored": False
                    },
                    "status": "FAILED",
                    "message": "Failed to update customer"
                },
                "err_details": {
                    "err_msg": str(e),
                    "err_type": "BUSSINESS-PROCESS-ERR"
                }
            }
    
    async def delete(self, session_cache) -> Dict[str, Any]:
        """Delete customer (soft delete)"""
        try:
            session_id = session_cache.session_id if hasattr(session_cache, 'session_id') else None
            
            return {
                "result": {
                    "response": {
                        "session_id": session_id
                    },
                    "status": "SUCCESS",
                    "message": "Customer deleted successfully"
                },
                "err_details": {}
            }
        except Exception as e:
            logger.error(f"Error deleting customer: {str(e)}")
            return {
                "result": {
                    "response": {
                        "session_id": session_cache.session_id if hasattr(session_cache, 'session_id') else None
                    },
                    "status": "FAILED",
                    "message": "Failed to delete customer"
                },
                "err_details": {
                    "err_msg": str(e),
                    "err_type": "BUSSINESS-PROCESS-ERR"
                }
            }
    async def get_customer_booking_map(self, session_cache, optiona_arg1, optional_arg2) -> Dict[str, Any]:
        """Get customer booking map"""
        try:
            from src.common.constants import SALON_BUSINESS_CUSTOMER_BOOKING_MAP_PATH
            
            customer_id = getattr(session_cache, "phone", None)
            session_id = getattr(session_cache, "session_id", None)
            business_id = getattr(session_cache, "business", None)
            
            booking_map_path = f"{SALON_BUSINESS_CUSTOMER_BOOKING_MAP_PATH}/{customer_id}.json"
            
            # Check if file exists
            if not os.path.exists(booking_map_path):
                error_msg = f"Customer booking map not found for customer_id: {customer_id}"
                return {
                    "result": {
                        "response": {
                            "session_id": session_id,
                            "business_id": business_id,
                            "customer_id": customer_id,
                            "customerbookingmap": {}
                        },
                        "status": "FAILED",
                        "message": error_msg
                    },
                    "err_details": {
                        "err_msg": error_msg,
                        "err_type": "BUSINESS-PROCESS-ERR"
                    }
                }
            
            # Read booking map data
            with open(booking_map_path, 'r') as f:
                booking_map_data = json.load(f)
            
            return {
                "result": {
                    "response": {
                        "session_id": session_id,
                        "business_id": business_id,
                        "customer_id": customer_id,
                        "customerbookingmap": booking_map_data
                    },
                    "status": "SUCCESS",
                    "message": "Customer booking map retrieved successfully"
                },
                "err_details": {}
            }
        
        except Exception as e:
            logger.error(f"Error retrieving customer booking map: {str(e)}")
            return {
                "result": {
                    "response": {
                        "session_id": getattr(session_cache, "session_id", None),
                        "business_id": getattr(session_cache, "business", None),
                        "customer_id": getattr(session_cache, "phone", None),
                        "customerbookingmap": {}
                    },
                    "status": "FAILED",
                    "message": f"Error retrieving customer booking map: {str(e)}"
                },
                "err_details": {
                    "err_msg": str(e),
                    "err_type": "BUSINESS-PROCESS-ERR"
                }
            }
    
    async def get(self, session_cache):
        pass
        return