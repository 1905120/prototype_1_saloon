"""
Business checker - validates phone and business fields, routes to appropriate handler
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


async def get_business_entity_context(
    phone: str,
    business: str,
    update_default: str,
    business_metadata_path: str,
    business_meta_schema: str
):
    """
    Initialize metadata paths for business, customer, and client
    
    Args:
        phone: Phone number
        business: Business name
        update_default: Default entity type
        business_metadata_path: Path to business metadata file
        business_meta_schema: Path to business metadata schema
    
    Returns:
        Tuple of (business_context, entity_context, entity_type, is_new_entity)
    """
    from src.core.context import BusinessContext

    business_context = BusinessContext(
        business=business,
        business_metadata_path=business_metadata_path,
        business_meta_schema=business_meta_schema
    )
    
    # Setup contexts based on phone mapping
    # load_entity_context=True means add phone mapping if not found
    business_context, entity_context, entity_type, is_new_entity = await setup_contexts(
        phone,
        business_context, 
        update_default=update_default,
        load_entity_context=True
    )
    
    return business_context, entity_context, entity_type, is_new_entity


class MainRequest(BaseModel):
    """Main request payload"""
    model_config = {"extra": "allow"}
    phone: str
    business: str
    name: Optional[str] = None
    updates: Optional[Dict[str, Any]] = None
    owner_name: Optional[str] = None
    salon_name: Optional[str] = None
    service_type: Optional[str] = None
    working_hours: Optional[list] = None
    data: Optional[Dict[str, Any]] = None  # Request data storage
    service_type: str
    operation_id: Optional[str] = None

def check_business(payload: Dict[str, Any]) -> bool:
    """
    Validate phone and business fields
    
    Args:
        payload: Request payload as dictionary
    
    Returns:
        True if phone and business are valid
    
    Raises:
        ValueError: If phone or business is invalid
    """
    # Validate phone field
    phone = payload.get("phone")
    if not phone:
        logger.error("Phone field is missing or empty from payload")
        raise ValueError("Phone field is required and cannot be empty")
    
    # Validate business field
    if "business" not in payload:
        logger.error("Business field is missing from payload")
        raise ValueError("Business field is required. Please specify business='salon'")
    
    business = payload.get("business")
    
    if business is None:
        logger.error("Business field value is None")
        raise ValueError("Business field cannot be empty. Please specify business='salon'")
    
    business_lower = str(business).lower().strip()
    
    if business_lower != "salon":
        logger.error(f"Invalid business type: {business}")
        raise ValueError(f"Only 'salon' business type is supported. Got: {business}")
    
    logger.info(f"Validation passed - Phone: {phone}, Business: {business_lower}")
    return True


async def setup_contexts(
    phone: str, 
    business_context, 
    update_default: str, 
    load_entity_context: bool = True
) -> tuple:
    """
    Setup business and entity contexts based on phone mapping
    
    Args:
        phone: Phone number from payload
        business_context: BusinessContext instance
        update_default: Default entity type if phone not found (determined by business type)
        load_entity_context: Whether to add phone mapping if not found (default: True)
        customer_metadata_path: Path to customer metadata file
        client_metadata_path: Path to client metadata file
    
    Returns:
        Tuple of (business_context, entity_context) or (business_context, None) if load_entity_context=False and phone not found
    """
    from src.core.context import CustomerContext, ClientContext
    
    # Get phone mapping from metadata manager
    # If not found and load_entity_context=True, updates cache according to update_default
    entity_type, is_new_entity = business_context.metadata_manager.get_phone_mapping(
        phone, 
        update_default=update_default,
        load_entity_context=load_entity_context
    )
    
    # If load_entity_context=False and phone not found, entity_type will be None
    if entity_type is None:
        logger.warning(f"Phone {phone} not found and load_entity_context=False, returning None for entity_context")
        return business_context, None
    
    logger.info(f"Phone {phone} identified as: {entity_type}")
    
    # Create appropriate context based on entity type
    if entity_type == "customer":
        entity_context = CustomerContext(business="salon")
        logger.info(f"Created CustomerContext for phone {phone}")
    elif entity_type == "client":
        entity_context = ClientContext(business="salon")
        logger.info(f"Created ClientContext for phone {phone}")
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")
        logger.warning(f"for {phone} entity type is set to default as {entity_type}")

    return business_context, entity_context, entity_type, is_new_entity


async def check_and_route_business(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Check business type and route to appropriate handler
    
    Args:
        payload: Request payload as dictionary
        background_tasks: FastAPI background tasks
    
    Returns:
        Response from handler
    
    Raises:
        HTTPException: If business type is invalid or routing fails
    """
    business_context = None
    phone = None
    
    try:
        # Validate payload
        check_business(payload)
        
        phone = payload.get("phone")
        business = payload.get("business", "").lower().strip()
        
        # Determine default entity type based on business
        
        if business == "salon":
            
            update_default = "customer"  # Default for salon business

            # Initialize BusinessContext for salon
        
            from src.common.constants import B_SALON_META_DATA_PATH, B_SALON_META_SCHEMA_PATH ,B_SALON_CUST_META_SCHEMA_PATH, B_SALON_CUST_META_DATA_PATH, B_SALON_CLIENT_META_SCHEM_PATH, B_SALON_CLIENT_META_DATA_PATH
            
            business_context, entity_context, entity_type, is_new_entity = await get_business_entity_context(phone, business, update_default, B_SALON_META_DATA_PATH, B_SALON_META_SCHEMA_PATH)
        
            # Parse payload for salon
            main_request = MainRequest(**payload)
            
            # Import and route to salon handler
            from src.business.salon.api import route_salon_request
            
            response = await route_salon_request(
                main_request,
                background_tasks,
                entity_context,
                entity_type,
                is_new_entity
            )
            if "status" in response and phone and response["status"] == "FAILED":
                business_context.metadata_manager._remove_phone_mapping(phone)
            return response
    
    except ValueError as e:
        logger.error(f"Payload validation error: {str(e)}")
        # Destroy business context and cleanup on validation error
        if business_context and phone:
            try:
                business_context.destroy(phone)
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Business routing error: {str(e)}", exc_info=True)
        # Destroy business context and cleanup on routing error
        if business_context and phone:
            try:
                business_context.destroy(phone)
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")
        raise HTTPException(status_code=500, detail=f"Error processing business request: {str(e)}")

