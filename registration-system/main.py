"""
Main entry point - FastAPI application with async routing
Routes requests to appropriate endpoints based on action
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from src.checkbusiness import check_and_route_business
from src.business.salon.api import router as salon_router
from src.payments.routes import router as payments_router
from src.chatbot_layer.api import router as chatbot_router
from src.chatbot_layer.business_number_api import router as business_number_router
import time

class Response(BaseModel):
    """Response containing result and error details"""
    model_config = {"extra": "allow"}
    result: Dict[str, Any]
    err_details: Dict[str, Any]


# ============ LIFESPAN ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    import logging
    import threading
    logger = logging.getLogger(__name__)
    
    # Startup
    try:
        from src.core.queue_manager import get_queue_manager
        from src.core.worker_pool import get_worker_pool
        from src.common.constants import MAX_WORKER_THREADS
        from src.errors.error_handler import ErrorStore
        
        logger.info("Startup: Initializing error store cache...")
        ErrorStore.clear_all_errors()
        logger.info("Startup: Error store cache initialized")
        
        logger.info("Startup: Initializing queue manager...")
        get_queue_manager()
        logger.info("Startup: Queue manager initialized")
        
        logger.info("Startup: Starting worker pool...")
        def start_workers():
            try:
                worker_pool = get_worker_pool(num_workers=MAX_WORKER_THREADS)
                worker_pool.start()
                logger.info(f"Startup: Worker pool started with {MAX_WORKER_THREADS} threads")
            except Exception as e:
                logger.error(f"Error starting worker pool: {str(e)}", exc_info=True)
        
        worker_thread = threading.Thread(target=start_workers, daemon=True)
        worker_thread.start()
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    try:
        from src.core.worker_pool import get_worker_pool
        get_worker_pool().stop()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)


app = FastAPI(title="Salon Prototype 2", version="1.0.0", lifespan=lifespan)

# Include routers
app.include_router(salon_router)
app.include_router(payments_router)
app.include_router(chatbot_router)
app.include_router(business_number_router)


# ============ MAIN ENDPOINTS ============
@app.post("/api/v1/getcustomerbookingmapping/{business_id}/{service_name}/{customer_id}", response_model=Response)
async def get_customer_booking_mapping(
    business_id: str,
    customer_id: str,
    service_name: str,
    background_tasks: BackgroundTasks,
    request: Request
) -> Response:
    """
    Get customer booking map with optional location details
    
    Args:
        business_id: Business ID (e.g., "salon")
        customer_id: Customer ID (phone number)
        service_name: Service name
        background_tasks: FastAPI background tasks
        request: Request body containing optional location details
    
    Returns:
        Response: Contains customer booking map data with location info
    """
    from src.errors.error_handler import ErrorStore, ErrorResponse
    
    payload = None
    try:
        from src.core.BusinessServiceManagement import business_service_cache
        from src.common.utils import parse_normal_time, get_current_normal_time
        # Get request body if provided
        body = {}
        try:
            body = await request.json()
        except:
            body = {}
        request_time = parse_normal_time(body["request_time"]) if "request_time" in body else get_current_normal_time()
        payload = {
            "business": business_id,
            "phone": customer_id,
            "action": "get-customer_booking_map",
            "service_name": service_name,
            "request_time" : request_time
        }
        
        # Add location details from request body if provided
        if "location" in body:
            payload["location"] = body["location"]
        
        # Get business service - initializes cache automatically if needed
        payload['operation_id'] = business_service_cache.get_operation_id(payload.get("business"), payload.get("service_name"))


        # Queue request to worker
        
        response = await check_and_route_business(
            payload,
            background_tasks
        )
        
        return response
    except Exception as e:
        phone = payload.get("phone", "unknown") if payload else "unknown"
        error_msg = str(e)
        ErrorStore.store(phone, error_msg, "SYSTEM-PROCESS-ERR")
        return ErrorResponse.build("SYSTEM-PROCESS-ERR", error_msg, f"Error processing request: {error_msg}")



@app.post("/api/v1/makerequest", response_model=Response)
async def make_request(request: Request, background_tasks: BackgroundTasks) -> Response:
    
    """
    Main entry point for all requests
    Routes to salon business handler and WAITS for response
    
    Args:
        payload: Request payload with action and data
        background_tasks: FastAPI background tasks
    
    Returns:
        Response: Contains session_id, status, and message with actual result
    """
    from src.errors.error_handler import ErrorStore, ErrorResponse
     
    try:
        # import time
        
        payload = await request.json()
        
        from src.core.BusinessServiceManagement import business_service_cache
        
        phone       = payload.get("phone", "unknown")
        business    = payload.get("business", None)
        service_name= payload.get("service_type", None)
        
        payload['operation_id'] = business_service_cache.get_operation_id(business, service_name)

        # Queue request to worker
        
        # Queue request to worker
        response = await check_and_route_business(
            payload,
            background_tasks
        )
        
        return response
    except Exception as e:
        phone = payload.get("phone", "unknown") if 'payload' in locals() else "unknown"
        error_msg = str(e)
        ErrorStore.store(phone, error_msg, "SYSTEM-PROCESS-ERR")
        return ErrorResponse.build("SYSTEM-PROCESS-ERR", error_msg, f"Error processing request: {error_msg}")

@app.middleware("http")
async def add_timing(request, call_next):
    start = time.time()
    response = await call_next(request)
    end = time.time()
    print("FULL REQUEST TIME:", (end-start)*1000, "ms")
    return response

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Configure logging for debug
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Uvicorn config with debug settings
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="debug",
        access_log=False,
        use_colors=True
    )
    
    server = uvicorn.Server(config)
    
    try:
        import asyncio
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print("\nServer shutdown requested")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
