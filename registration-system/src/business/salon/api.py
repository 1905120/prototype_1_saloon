"""
Salon API endpoints - specific operations for customers and clients
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union, List, Callable
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

class SessionCache_Customer:
    """Session data object"""
    
    def __init__(self, session_dict: Dict[str, Any]):
        self.id = session_dict.get("id")
        self.name = session_dict.get("name")
        self.email = session_dict.get("email")
        self.phone = session_dict.get("phone")
        self.dateOfBirth = session_dict.get("dateOfBirth")
        self.address = session_dict.get("address")
        self.location = session_dict.get("location")
        self.version = session_dict.get("version")
        self.action = session_dict.get("action")
        self.approvalStatus = session_dict.get("approvalStatus")
        self.updatedAt = session_dict.get("session_created_at")
        self.updatedFields = session_dict.get("updatedFields")
        self.registeredAt = session_dict.get("registeredAt")
        self.business = session_dict.get("business")
        self.service_type = session_dict.get("service_type")
        self.live_record_path = session_dict.get("live_record_path")
        self.create_schema_path = session_dict.get("create_schema_path")
        self.session_id = session_dict.get("session_id")
        self.entity_id = session_dict.get("entity_id")
        self.phone = session_dict.get("phone")
        self.operation_type = session_dict.get("operation_type") #action
        self.operation = session_dict.get("operation") #function
        self.operation_id = session_dict.get("operation_id") #service id for the business
        self.latest_version_record_id = session_dict.get("latest_version_record_id")
        self.process_context = session_dict.get("process_context")
        
class SessionCache_Client:
    """Session data object"""
    
    def __init__(self, session_dict: Dict[str, Any]):
        """
        Initialize session data from dictionary
        
        Args:
            session_dict: Dictionary containing session information
        """
        self.session_id = session_dict.get("session_id")
        self.entity_id = session_dict.get("entity_id")
        self.latest_version_record_id = session_dict.get("latest_version_record_id")

        self.live_record_path = session_dict.get("live_record_path")
        self.create_schema_path = session_dict.get("create_schema_path")
        
        self.process_context = session_dict.get("process_context")

        self.id = session_dict.get("phone")
        self.clientId = session_dict.get("phone")
        self.ownerName = session_dict.get("ownerName")
        self.phone = session_dict.get("phone")
        self.email = session_dict.get("email")
        self.ownerAddress = session_dict.get("ownerAddress")
        self.salonName = session_dict.get("salonName")
        self.business = session_dict.get("business")
        self.salonAddress = session_dict.get("salonAddress")
        self.serviceType = session_dict.get("serviceType")
        self.services = session_dict.get("services")
        self.workingHours = session_dict.get("workingHours")
        self.weeklyHoliday = session_dict.get("weeklyHoliday")
        self.location = session_dict.get("location")
        self.isOpen = session_dict.get("isOpen")
        self.slots = session_dict.get("slots")
        self.licence = session_dict.get("licence")
        self.version = session_dict.get("version")
        self.action = session_dict.get("action")
        self.approvalStatus = session_dict.get("approvalStatus")
        self.updatedAt = session_dict.get("session_created_at")
        self.updatedFields = session_dict.get("updatedFields")
        self.registeredAt = session_dict.get("registeredAt")
        self.operation = session_dict.get("operation") #function
        self.operation_type = session_dict.get("operation_type") #action
        self.process_context = session_dict.get("process_context")

class SessionCache_GetCustomerSuggestion:
    """Session data object"""
    
    def __init__(self, session_dict: Dict[str, Any]):
        """
        Initialize session data from dictionary
        
        Args:
            session_dict: Dictionary containing session information
        """
        self.session_id = session_dict.get("session_id")
        self.phone = session_dict.get("phone")
        self.action = session_dict.get("action")
        self.business = session_dict.get("business")
        self.operation = session_dict.get("operation")
        self.operation_type = session_dict.get("operation_type") #action
        self.operation_id = session_dict.get("operation_id")
        self.id = session_dict.get("id")
        self.process_context = session_dict.get("process_context")
        self.location = session_dict.get("location")
        self.request_time = session_dict.get("request_time")

class MainRequestClient(BaseModel):
    """Main request payload"""
    model_config = {"extra": "allow"}
    clientId: Optional[str] = None
    ownerName: str
    phone: str
    email: Optional[str] = None
    ownerAddress: Optional[str] = None
    salonName: Optional[str] = None
    business: str
    salonAddress: Optional[str] = None
    serviceType: Optional[list] = []
    workingHours: Optional[list] = []
    weeklyHoliday: Optional[list] = []
    location: Optional[dict] = {}
    isOpen: Optional[bool] = None
    slots: Optional[dict] = {}
    licence: Optional[str] = None
    version: Optional[int] =  None
    action: Optional[str] = None
    approvalStatus: Optional[str] = None
    updatedAt: Optional[str] = None
    updatedFields: Optional[None] = []
    registeredAt: Optional[str] = ""
    services:Optional[dict] = []

    #system defined
    handler_func: Callable[..., Any] = None
    action: Optional[str] = None
    session_id: Optional[str] = None
    latest_version: Optional[int] = None
    latest_version_record_id: Optional[str] = None

class MainRequestCustomer(BaseModel):
    """Main request payload"""
    model_config = {"extra": "allow"}
    customer_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: str
    dateOfBirth: Optional[str] = None
    address: Optional[str] = None
    location: Optional[dict] = None
    version: Optional[int] = None
    action: Optional[str] = None
    approvalStatus: Optional[str] = None
    updatedAt: Optional[str] = None
    updatedFields: Optional[str] = None
    registeredAt: Optional[str] = None
    business: str
    service_type: str
    operation_id: Optional[str] = None
    #system defined
    handler_func: Callable[..., Any] = None
    action: Optional[str] = None
    session_id: Optional[str] = None
    latest_version: Optional[int] = None
    latest_version_record_id: Optional[str] = None

class MainRequestCustomerBookingMap(BaseModel):
    """Request payload for getting customer booking map"""
    model_config = {"extra": "allow"}
    phone: str
    business: str

    #system defined
    handler_func: Callable[..., Any] = None
    action: Optional[str] = None
    latest_version_record_id : str = ""
    location: dict = {}
    request_time: str

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
            function = customer.get_customer_suggestions
            action = "get-customer_booking_map"
    if action and function:
        logger.info(f"Got handler function for action: {action}")
    #return a updated payload
    payload.handler_func = function
    payload.action = action

    return payload


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
            payload = _get_handler_function(entity_type, is_new_entity, payload)
            if not payload.handler_func:
                error_msg = f"No handler found for action: {payload.action}"
                ErrorStore.store(payload.phone, error_msg, "SYSTEM-PROCESS-ERR")
                return ErrorResponse.build("SYSTEM-PROCESS-ERR", error_msg, error_msg)
            
            logger.info(f"Got handler function for action: {payload.action}")
            
            system_context = {}
            # Create a minimal context for SYSTEM operations
            from src.core.context import CustomerContext, ClientContext
            system_context["customer_context"] = CustomerContext(business="salon")
            system_context["client_context"]   = ClientContext(business="salon")
            # system_context.phone = payload.phone
            # system_context.business = payload.business
            # system_context.session_id = str(uuid.uuid4())
            
            # Process through session manager
            session_manager = SessionManager(entity_type, system_context, payload)
            response = await session_manager.process()
            
            # logger.info(f"Successfully routed {payload.action} for salon - Session: {response.get('session_id')}")
            return response
        
        # Get cache data
        elif entity_type == "customer":
            cache_data = entity_context.customer_manager.get_all()
            logger.info(f"Retrieved cache for {entity_type}")

        elif entity_type == "client":
            cache_data = entity_context.client_manager.get_all()
            logger.info(f"Retrieved cache for {entity_type}")
        
        payload = _get_handler_function(entity_type, is_new_entity, payload)

        #just a safe check whether entity cache loaded properly else initise a entity cache for the customer
        await check_entity_key_in_cache(payload, entity_type, entity_context, cache_data)
            
        if not payload.handler_func:
            error_msg = f"No handler found for action: {entity_context._action}"
            ErrorStore.store(payload.phone, error_msg, "SYSTEM-PROCESS-ERR")
            return ErrorResponse.build("SYSTEM-PROCESS-ERR", error_msg, error_msg)
        
        # Process through session manager
        session_manager = SessionManager(entity_type, entity_context, payload)
        response = await session_manager.process()
        
        logger.info(f"Successfully routed {payload.action} for salon - Session: {response.get('session_id')}")
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
