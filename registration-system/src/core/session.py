"""
Session management with integrated response fetching
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import threading
from src.common.enums import OperationType, PipelineStatus
from src.errors.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session lifecycle with metadata tracking and response fetching"""
    
    # Class-level response cache and events
    _response_cache = {}
    _cache_lock = threading.Lock()
    _response_events = {}
    
    def __init__(self, entity_type, entity_context, payload):
        """
        Initialize session manager
        
        Args:
            entity_type: Type of entity ("customer" or "client")
            handler_func: Handler function for the operation
            entity_context: Entity context (CustomerContext or ClientContext)
            payload: Request payload
        """
        self.sessions = {}
        self.entity_type = entity_type  # "customer" or "client"
        self.entity_context = entity_context
        self.payload = payload
        self.Err = None
        self.entity_id = None

    def create_session(self):
            
            self.session_id = str(uuid.uuid4())

            self.update_entity_meta_data()
            
            from src.common.constants import SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH, SALON_BUSINESS_SYSTEM_ACTIONS, SALON_BUSINESS_CLIENT_LIVE_DATA_PATH, B_SALON_CUST_CREATE_SCHEM_PATH, B_SALON_CLIENT_CREATE_SCHEM_PATH
            from src.core.BusinessServiceManagement import business_service_cache
            if self.entity_type == "customer":
                self.sessions = {
                                    "action": self.payload.action,
                                    "session_id": self.session_id,
                                    "entity_id" : self.entity_id,
                                    "phone": self.payload.phone,
                                    "operation_type": self.payload.action,
                                    "status": None,
                                    "operation": self.payload.handler_func,
                                    "session_created_at": datetime.now().isoformat(),
                                    "process_result": None,
                                    "error": [],
                                    "session_finished_at" : None,
                                    "operation_id": self.payload.operation_id,
                                    "business":self.payload.business,
                                    "latest_version_record_id" : self.payload.latest_version_record_id,
                                    "name": self.payload.name,
                                    "email": self.payload.email,
                                    "location": self.payload.location,
                                    "address": self.payload.address,
                                    "dataOfBirth": self.payload.dateOfBirth,
                                    "version" : self.payload.latest_version,
                                    "live_record_path" : SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH,
                                    "create_schema_path" : B_SALON_CUST_CREATE_SCHEM_PATH,
                                    "operation_id" : self.payload.operation_id
                                }
            elif self.entity_type == "client":
                self.sessions = {
                                    "session_id": self.session_id,
                                    "clientId" : self.entity_id,
                                    "entity_id" : self.entity_id,
                                    "ownerName" : self.payload.ownerName,
                                    "phone" : self.payload.phone,
                                    "email" : self.payload.email,
                                    "ownerAddress" : getattr(self.payload, "ownerAddress", []),
                                    "salonName": getattr(self.payload, "salonName", []),
                                    "business" : self.payload.business,
                                    "salonAddress" : getattr(self.payload, "salonAddress", ""),
                                    "serviceType" : getattr(self.payload, "serviceType", []),
                                    "workingHours" : getattr(self.payload, "serviceType", []),
                                    "weeklyHoliday" : getattr(self.payload, "weeklyHoliday", []),
                                    "location": getattr(self.payload, "location"),
                                    "isOpen": getattr(self.payload, "isOpen", None),
                                    "slots": getattr(self.payload, "slots", [{}]),
                                    "licence": getattr(self.payload, "licence", ""),
                                    "version": self.payload.latest_version,
                                    "action": getattr(self.payload, "action", None),
                                    "approvalStatus": None,
                                    "updatedAt": None,
                                    "updatedFields": None,
                                    "registeredAt": None,
                                    "operation_type": self.payload.action,
                                    "operation": self.payload.handler_func,
                                    "operation_id": getattr(self.payload, "action", None),
                                    "latest_version_record_id" : self.payload.latest_version_record_id,
                                    "live_record_path" : SALON_BUSINESS_CLIENT_LIVE_DATA_PATH,
                                    "create_schema_path" : B_SALON_CLIENT_CREATE_SCHEM_PATH,
                                    "services" : self.payload.services,
                                    "salonName" : self.payload.salonName
                                }
            elif self.entity_type == "SYSTEM" and self.payload.action in SALON_BUSINESS_SYSTEM_ACTIONS:
                self.sessions = {
                                    "action"   : self.payload.action,
                                    "phone"    : self.payload.phone,
                                    "business" : self.payload.business,
                                    "operation": self.payload.handler_func,
                                    "operation_id" : self.payload.operation_id,
                                    "id"       : self.payload.phone,
                                    "session_id": self.session_id,
                                    "process_context" : self.entity_context,
                                    "operation_type": self.payload.action,
                                    "location" : self.payload.location,
                                    "request_time" : self.payload.request_time
                                }

            return
    
    async def process(self):
        from src.errors.error_handler import ErrorStore, ErrorResponse
        
        response = None
        try:
            session_cache = self.pre_process()
            
            if not session_cache:
                error_msg = "Failed to create session"
                ErrorStore.store(self.payload.phone, error_msg, "SYSTEM-PROCESS-ERR")
                return ErrorResponse.build("SYSTEM-PROCESS-ERR", error_msg, error_msg, {"session_id": self.session_id})

            queue_success = self.session_queue_manager(session_cache)
            
            if not queue_success:
                error_msg = "Failed to queue session"
                ErrorStore.store(self.payload.phone, error_msg, "SYSTEM-PROCESS-ERR")
                return ErrorResponse.build("SYSTEM-PROCESS-ERR", error_msg, error_msg, {"session_id": self.session_id})

            response = self.post_process()

        except Exception as e:
            self.Err = str(e)
            ErrorStore.store(self.payload.phone, str(e), "SYSTEM-PROCESS-ERR")
            response = ErrorResponse.build("SYSTEM-PROCESS-ERR", str(e), f"Error processing session: {str(e)}", {"session_id": self.session_id})
        
        return response
    
    def pre_process(self) -> Optional[Any]:
        """Load session from storage and create session data object"""
        from src.errors.error_handler import ErrorStore
        from src.business.salon.api import SessionCache_Client, SessionCache_Customer, SessionCache_GetCustomerSuggestion
        
        # Create session
        self.create_session()

        if not self.sessions: #this is the session cache
            error_msg = "session cache not found"
            ErrorStore.store(self.payload.phone, error_msg, "SYSTEM-PROCESS-ERR")
            logger.error(error_msg)
            return None
        
        # Create a session data object from stored session
        SessionData = None
        if self.payload.business == "salon" and self.entity_type == "client":
            SessionData = SessionCache_Client(self.sessions)
        if self.payload.business == "salon" and self.entity_type == "customer":
            SessionData = SessionCache_Customer(self.sessions)
        if self.payload.business == "salon" and self.entity_type == "SYSTEM":
            SessionData = SessionCache_GetCustomerSuggestion(self.sessions)

        return SessionData

    def post_process(self) -> Dict[str, Any]:
        """
        Post-process: prepare final response
        
        Returns:
            Response dictionary with session details
        """

        response = self.wait_and_get_response(self.session_id)

        if getattr(self.payload, "action", None) != "get-customer_booking_map":
            if response["result"]["status"] == "FAILED" and not response["result"]["response"]["isRecordStored"]:
                if self.entity_type == "customer":
                    is_removed = self.entity_context.customer_manager.remove_customer_entry(self.sessions["phone"])

        return response
    
    def update_entity_meta_data(self):

        if self.entity_type == "customer":
            meta_data = self.entity_context.customer_manager.get_all()
            customers = meta_data["customer"]
            
            if not customers[self.payload.phone]["customer_id"]:
                self.payload.entity_meta_key = self.payload.phone
                customers[self.payload.phone]["customer_id"] = self.payload.entity_meta_key
                meta_data["metadata"]["total_customers"] += 1
            # else:
            #     self.payload.entity_meta_key = customers[self.payload.phone]["customer_id"]
            
            version_no = customers[self.payload.phone]["latest_latest_version"]
            if "versions" in customers[self.payload.phone] and customers[self.payload.phone]["versions"]:
                if version_no in customers[self.payload.phone]["versions"]:
                    self.payload.latest_version_record_id = customers[self.payload.phone]["versions"][version_no]

            version_no += 1
            self.payload.latest_version = version_no
            self.entity_id = f'{self.payload.business}#{self.payload.operation_id}#{self.session_id}'
            
            customers[self.payload.phone]["latest_latest_version"] = version_no
            customers[self.payload.phone]["versions"][version_no] = self.entity_id
            if self.payload.action != "get-customer_booking_map":
                self.entity_context.customer_manager.put_all(meta_data)
        elif self.entity_type == "client":
            meta_data = self.entity_context.client_manager.get_all()
            client = meta_data["client"]
            
            if not client[self.payload.phone]["client_id"]:
                self.payload.entity_meta_key = self.payload.phone
                client[self.payload.phone]["client_id"] = self.payload.entity_meta_key
                meta_data["metadata"]["total_clients"] += 1
            version_no = client[self.payload.phone]["latest_latest_version"]
            if "versions" in client[self.payload.phone] and client[self.payload.phone]["versions"]:
                if version_no in client[self.payload.phone]["versions"]:
                    self.payload.latest_version_record_id = client[self.payload.phone]["versions"][version_no]
            version_no += 1
            self.payload.latest_version = version_no
            self.entity_id = f'{self.payload.phone}#{self.payload.business}#{version_no}'
            client[self.payload.phone]["latest_latest_version"] = version_no
            client[self.payload.phone]["versions"][version_no] = self.entity_id

            self.entity_context.client_manager.put_all(meta_data)
        return


    def clear_entity_meta_data_on_fail(self, phone):

        if self.entity_type == "customer":
            self.entity_context.customer_manager.remove_entry(phone)
        return
        
    def session_queue_manager(self, session_cache) -> bool:
        """
        Add session to queue for worker processing
        
        Args:
            session_cache: SessionData object to queue
        
        Returns:
            True if successful, False otherwise
        """
        from src.errors.error_handler import ErrorStore
        
        try:
            from src.core.queue_manager import get_queue_manager
            
            queue_manager = get_queue_manager()
            
            # Set initial status to QUEUED
            queue_manager.set_status(
                self.session_id,
                "QUEUED",
                "Request queued for processing",
                0
            )
            
            # Add SessionData object to queue
            queue_manager.put_to_queue(session_cache)
            logger.info(f"Session {self.session_id} added to queue for processing")
            return True
            
        except Exception as e:
            logger.error(f"Error adding session to queue: {str(e)}", exc_info=True)
            ErrorStore.store(self.payload.phone, str(e), "SYSTEM-PROCESS-ERR")
            return False
    
    @classmethod
    def put_response(cls, session_id: str, response: Dict[str, Any]) -> None:
        """
        Cache a response
        
        Args:
            session_id: Session ID
            response: Response data to cache
        """
        with cls._cache_lock:
            cls._response_cache[session_id] = response
            logger.info(f"Response cached for session {session_id}")
            
            # Signal waiting thread if exists
            if session_id in cls._response_events:
                cls._response_events[session_id].set()
    
    @classmethod
    def wait_and_get_response(cls, session_id: str, timeout: float = 60) -> Dict[str, Any]:
        """
        Wait for and retrieve response from cache
        
        Args:
            session_id: Session ID
            timeout: Timeout in seconds
        
        Returns:
            Response data
        """
        event = threading.Event()
        
        with cls._cache_lock:
            cls._response_events[session_id] = event
            
            # Return if already cached
            if session_id in cls._response_cache:
                response = cls._response_cache.pop(session_id)
                logger.info(f"Response retrieved for session {session_id}")
                return response
        
        # Wait for response
        if event.wait(timeout=timeout):
            with cls._cache_lock:
                if session_id in cls._response_cache:
                    response = cls._response_cache.pop(session_id)
                    logger.info(f"Response retrieved for session {session_id}")
                    return response
        
        # Timeout
        logger.warning(f"Response timeout for session {session_id}")
        return {
            "result": {
                "response": {
                    "session_id": session_id
                },
                "status": "FAILED",
                "message": f"Response not received within {timeout}s"
            },
            "err_details": {
                "err_msg": "Request timeout",
                "err_type": "SYSTEM-PROCESS-ERR"
            }
        }