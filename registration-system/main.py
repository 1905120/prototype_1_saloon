"""
Main entry point - FastAPI application with async routing
Routes requests to appropriate endpoints based on action
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from src.checkbusiness import check_and_route_business
from src.business.salon.api import router as salon_router

# # ============ REQUEST MODELS ============
# class MakeRequestPayload(BaseModel):
#     """Generic request payload for /api/v1/makerequest"""
    
#     model_config = {"extra": "allow"}
#     action: str = None
#     phone: str
#     business: str
#     name: Optional[str] = None
#     updates: Optional[Dict[str, Any]] = None
#     owner_name: Optional[str] = None
#     salon_name: Optional[str] = None
#     service_type: Optional[str] = None
#     working_hours: Optional[list] = None
#     service_type: str
#     operation_id: Optional[str] = None

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
        # from src.core.BusinessServiceManagement import business_service_cache
        
        # logger.info("Startup: Initializing business service cache...")
        # business_service_cache.initialize_cache(business_name="business_service")
        # logger.info("Startup: Business service cache initialized")
        
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


# Initialize FastAPI app with lifespan
app = FastAPI(title="Salon Prototype 2", version="1.0.0", lifespan=lifespan)

# Include salon router
app.include_router(salon_router)


# ============ MAIN ENDPOINTS ============
@app.get("/api/v1/getcustomerbookingmapping/{business_id}/{customer_id}", response_model=Response)
async def get_customer_booking_mapping(business_id: str, customer_id: str, background_tasks: BackgroundTasks) -> Response:
    """
    Get customer booking map
    
    Args:
        business_id: Business ID (e.g., "salon")
        customer_id: Customer ID (phone number)
        background_tasks: FastAPI background tasks
    
    Returns:
        Response: Contains customer booking map data
    """
    from src.errors.error_handler import ErrorStore, ErrorResponse
    import json
    import os
    
    try:
        from src.common.constants import SALON_BUSINESS_CUSTOMER_BOOKING_MAP_PATH
        
        payload = {
                        "business"   : business_id,
                        "phone"      : customer_id,
                        "action"     : "get-customer_booking_map"
                    }
        
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
        payload = await request.json()

        from src.core.BusinessServiceManagement import business_service_cache
        
        phone = payload.get("phone", "unknown")
        
        # Get business service - initializes cache automatically if needed
        payload['operation_id'] = business_service_cache.get_operation_id(payload['business'], payload['service_type'])

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
        access_log=True,
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
