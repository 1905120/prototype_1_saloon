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
    if action == "create-customer":
        schema_path = B_SALON_CUST_CREATE_SCHEM_PATH
    elif action == "update-customer":
        schema_path = B_SALON_CUST_UPDATE_SCHEM_PATH

    missing_fields, schema = validate_against_schema(schema_path, data)

    if not TEST and missing_fields:
        raise Exception("Refer schema - {}. Invalid payload passed for action {}!!!".format(schema_path, action))
    
    data = create_dict_structure(schema, data, action)

    return data

class Customer:
    """Customer business logic handler"""
    
    async def create(self, session_cache) -> Dict[str, Any]:
        """Create new customer"""
        try:
            session_id = session_cache.session_id if hasattr(session_cache, 'session_id') else None
            
            return {
                "session_id": session_id,
                "status": "SUCCESS",
                "message": "Customer created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise
    
    async def update(self, session_cache):
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
                "session_id": session_id,
                "status": "SUCCESS",
                "business": session_cache.business,
                "cust_id": session_cache.entity_id,
                "service_id":session_cache.operation_id,
                "message": "Customer updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            return {
                "session_id": session_cache.session_id if hasattr(session_cache, 'session_id') else None,
                "status": "FAILED",
                "message": "Failed to update customer"
            }
    
    async def delete(self, session_cache) -> Dict[str, Any]:
        """Delete customer (soft delete)"""
        try:
            session_id = session_cache.session_id if hasattr(session_cache, 'session_id') else None
            
            return {
                "session_id": session_id,
                "status": "SUCCESS",
                "message": "Customer deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting customer: {str(e)}")
            return {
                "session_id": session_cache.session_id if hasattr(session_cache, 'session_id') else None,
                "status": "FAILED",
                "message": "Failed to delete customer"
            }
