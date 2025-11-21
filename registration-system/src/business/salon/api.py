"""
Salon API endpoints - specific operations for customers and clients
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union, List
from src.core.session import SessionManager
from src.business.salon.customer import Customer
from src.business.salon.client import Client
import logging
import uuid
from src.core.pipeline import DataPipeline
from src.business.salon.customer import validate_and_load_payload

logger = logging.getLogger(__name__)

# Create router for v1 endpoints
router = APIRouter(prefix="/v1", tags=["v1"])

# Module-level objects
customer = Customer()
client = Client()
# SessionManager will be initialized in route_salon_request

class MainRequestClient(BaseModel):
    """Main request payload"""
    model_config = {"extra": "allow"}
    phone: str
    business: str
    name: Optional[str] = None
    updates: Optional[Dict[str, Any]] = None
    owner_name: Optional[str] = None
    salon_name: Optional[str] = None
    working_hours: Optional[list] = None
    data: Optional[Dict[str, Any]] = None  # Request data storage
    service_type: str
    operation_id: Optional[str] = None
    action: Optional[str] = None

class MainRequestCustomer(BaseModel):
    """Main request payload"""
    model_config = {"extra": "allow"}
    _id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: str
    dateOfBirth: Optional[str] = None
    address: Optional[str] = None
    locations: Optional[List[str]] = None
    version: Optional[list] = None
    action: Optional[str] = None
    approvalStatus: Optional[str] = None
    updatedAt: Optional[str] = None
    updatedFields: Optional[str] = None
    registeredAt: Optional[str] = None
    business: str
    service_type: str
    operation_id: Optional[str] = None


class MainRequestCustomerBookingMap(BaseModel):
    """Request payload for getting customer booking map"""
    model_config = {"extra": "allow"}
    phone: str
    business: str
    action: Optional[str] = None
    

class SessionResponse(BaseModel):
    """Response containing session ID"""
    session_id: str
    status: str
    message: str

def _get_handler_function(entity_type, is_new_entity, payload):
    """Get handler function based on entity type and whether it's new"""
    function = None
    action = None
    from src.common.constants import SALON_BUSINESS_SYSTEM_ACTIONS
    if entity_type == "customer":
        if is_new_entity:
            action = "create"
            function = customer.create
        elif payload.action == "update":
            action = "update-customer"
            function = customer.update
        elif payload.action == "get-customer":
            action = "get-customer"
            function == customer.get
        else:
            action = "create-customer"
            function = customer.create
    elif entity_type == "client":
        if is_new_entity:
            action = "create-client"
            function = client.create
        else:
            action = "update-client"
            function = client.update
    elif entity_type == "SYSTEM":
        if payload.action == "get-customer_booking_map":
            function = customer.get_customer_booking_map
            action = payload.action
    return function, action


async def check_entity_key_in_cache(payload, entity_type, entity_context, cache_data):
    """Check if entity exists in cache, create if not"""
    entity_key = payload.phone
    if entity_key in cache_data[entity_type]:
        entity_id = cache_data[entity_type][entity_key].get("customer_id" if entity_type == "customer" else "client_id")
        logger.info(f"Entity found in cache with id: {entity_id}")
    else:
        if entity_type == "customer":
            cache_data[entity_type][entity_key] = {
                "customer_id": None,
                "latest_latest_version": 0,
                "versions": {}
            }
            entity_context.customer_manager.put_all(cache_data)
        else:
            cache_data[entity_type][entity_key] = {
                "client_id": None,
                "latest_latest_version": 0,
                "versions": {}
            }
            entity_context.client_manager.put_all(cache_data)
        logger.info(f"Created new entity in cache with key: {entity_key}")
    return
# ============ ROUTING ============
async def route_salon_request(
    payload: Union[MainRequestCustomer, MainRequestClient],
    background_tasks: BackgroundTasks,
    entity_context,
    entity_type,
    is_new_entity,
    business_context=None
) -> Dict[str, Any]:
    """
    Route salon request to appropriate handler based on action
    
    Args:
        payload: Salon request payload
        background_tasks: FastAPI background tasks
        entity_context: CustomerContext or ClientContext based on phone mapping
        business_context: (Optional) BusinessContext instance for business-level operations (default: None)
    
    Returns:
        Response from handler
    """
    from src.errors.error_handler import ErrorStore, ErrorResponse
    
    try:
        # logger.info(f"Routing salon request for action: {payload.action}")
        logger.info(f"Entity context type: {type(entity_context).__name__ if entity_context else 'None'}")
        
        # Handle SYSTEM entity type (e.g., get-customer_booking_map)
        if entity_type == "SYSTEM":
            handler_func, action = _get_handler_function(entity_type, is_new_entity, payload)
            if not handler_func:
                error_msg = f"No handler found for action: {payload.action}"
                ErrorStore.store(payload.phone, error_msg, "SYSTEM-PROCESS-ERR")
                return ErrorResponse.build("SYSTEM-PROCESS-ERR", error_msg, error_msg)
            
            logger.info(f"Got handler function for action: {action}")
            
            # Create a minimal context for SYSTEM operations
            from src.core.context import CustomerContext
            system_context = CustomerContext(business="salon")
            system_context.phone = payload.phone
            system_context.business = payload.business
            system_context.session_id = str(uuid.uuid4())
            
            # Process through session manager
            session_manager = SessionManager(entity_type, handler_func, system_context, payload=payload)
            response = await session_manager.process()
            
            logger.info(f"Successfully routed {action} for salon - Session: {response.get('session_id')}")
            return response
        
        # Get cache data
        if entity_type == "customer":
            cache_data = entity_context.customer_manager.get_all()
            logger.info(f"Retrieved cache for {entity_type}")
        elif entity_type == "client":
            cache_data = entity_context.client_manager.get_all()
            logger.info(f"Retrieved cache for {entity_type}")
        
        handler_func, action = _get_handler_function(entity_type, is_new_entity, payload)

        if entity_type in ["customer"]:
            # Check/create entity in cache
            await check_entity_key_in_cache(payload, entity_type, entity_context, cache_data)
            entity_context.customer_name = getattr(payload, "name", None)
            entity_context.email         = getattr(payload, "email", None)
            entity_context.location      = getattr(payload, "location", None)
            entity_context.address       = getattr(payload, "address", None)
            entity_context.date_of_birth = getattr(payload, "dateOfBirth", None)

            payload = validate_and_load_payload(action, payload)

            entity_context._action       = action
            
        if not handler_func:
            error_msg = f"No handler found for action: {entity_context._action}"
            ErrorStore.store(payload.phone, error_msg, "SYSTEM-PROCESS-ERR")
            return ErrorResponse.build("SYSTEM-PROCESS-ERR", error_msg, error_msg)
        
        logger.info(f"Got handler function for action: {action}")
        
        # Process through session manager
        session_manager = SessionManager(entity_type, handler_func, entity_context, payload=payload)
        response = await session_manager.process()
        
        logger.info(f"Successfully routed {action} for salon - Session: {response.get('session_id')}")
        return response
    
    except Exception as e:
        logger.error(f"Routing error: {str(e)}", exc_info=True)
        ErrorStore.store(payload.phone, str(e), "SYSTEM-PROCESS-ERR")
        return ErrorResponse.build("SYSTEM-PROCESS-ERR", str(e), f"Error routing request: {str(e)}")


# ============ PLACEHOLDER ENDPOINTS ============
@router.get("/health")
async def health():
    """Health check for salon API"""
    return {
        "result": {
            "response": {},
            "status": "SUCCESS",
            "message": "Health check passed"
        },
        "err_details": {}
    }
