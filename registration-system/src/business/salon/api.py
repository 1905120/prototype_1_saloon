"""
Salon API endpoints - specific operations for customers and clients
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from src.checkbusiness import MainRequest
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


class SessionResponse(BaseModel):
    """Response containing session ID"""
    session_id: str
    status: str
    message: str

def _get_handler_function(entity_type: str, is_new_entity: bool):
    """Get handler function based on entity type and whether it's new"""
    function = None
    action = None
    
    if entity_type == "customer":
        if is_new_entity:
            action = "create-customer"
            function = customer.create
        else:
            action = "update-customer"
            function = customer.update
    elif entity_type == "client":
        if is_new_entity:
            action = "create-client"
            function = client.create
        else:
            action = "update-client"
            function = client.update
    
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
                "versions": []
            }
            entity_context.customer_manager.put_all(cache_data)
        else:
            cache_data[entity_type][entity_key] = {
                "client_id": None,
                "latest_latest_version": 0,
                "versions": []
            }
            entity_context.client_manager.put_all(cache_data)
        logger.info(f"Created new entity in cache with key: {entity_key}")
    return
# ============ ROUTING ============
async def route_salon_request(
    payload: MainRequest,
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
    
    Raises:
        HTTPException: If action is invalid or handler fails
    """
    try:
        # logger.info(f"Routing salon request for action: {payload.action}")
        logger.info(f"Entity context type: {type(entity_context).__name__}")
        
        # Determine entity type from action
        # action = payload.action.lower()
        # if "customer" in action:
        #     entity_type = "customer"
        # elif "client" in action:
        #     entity_type = "client"
        # else:
        #     raise ValueError(f"Invalid action: {action}")
        
        # logger.info(f"Processing {entity_type} operation: {action}")
        
        # Get cache data
        if entity_type == "customer":
            cache_data = entity_context.customer_manager.get_all()
        else:
            cache_data = entity_context.client_manager.get_all()
        
        logger.info(f"Retrieved cache for {entity_type}")
        
        # Check/create entity in cache
        await check_entity_key_in_cache(payload, entity_type, entity_context, cache_data)
        
        # Get handler function
        handler_func, action = _get_handler_function(entity_type, is_new_entity)
        
        payload = validate_and_load_payload(action, payload)

        entity_context._action = action
        
        if not handler_func:
            raise ValueError(f"No handler found for action: {entity_context._action}")
        
        logger.info(f"Got handler function for action: {entity_context._action}")
        
        # Process through session manager
        session_manager = SessionManager(entity_type, handler_func, entity_context, payload=payload)
        response = await session_manager.process()
        
        logger.info(f"Successfully routed {entity_context._action} for salon - Session: {response.get('session_id')}")
        return response
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Routing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error routing request: {str(e)}")


# ============ PLACEHOLDER ENDPOINTS ============
@router.get("/health")
async def health():
    """Health check for salon API"""
    return {"status": "ok"}
