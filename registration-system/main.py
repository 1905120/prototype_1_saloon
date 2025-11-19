"""
Main entry point - FastAPI application with async routing
Routes requests to appropriate endpoints based on action
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from src.checkbusiness import check_and_route_business

# ============ REQUEST MODELS ============
class MakeRequestPayload(BaseModel):
    """Generic request payload for /api/v1/makerequest"""
    
    model_config = {"extra": "allow"}
    action: str = None
    phone: str
    business: str
    name: Optional[str] = None
    updates: Optional[Dict[str, Any]] = None
    owner_name: Optional[str] = None
    salon_name: Optional[str] = None
    service_type: Optional[str] = None
    working_hours: Optional[list] = None
    service_type: str
    operation_id: Optional[str] = None

class Response(BaseModel):
    """Response containing session ID"""
    session_id: str
    status: str
    message: str


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
        # from src.core.BusinessServiceManagement import business_service_cache
        
        # logger.info("Startup: Initializing business service cache...")
        # business_service_cache.initialize_cache(business_name="business_service")
        # logger.info("Startup: Business service cache initialized")
        
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


# ============ MAIN ENDPOINT ============
@app.post("/api/v1/makerequest", response_model=Response)
async def make_request(payload: MakeRequestPayload, background_tasks: BackgroundTasks) -> Response:
    """
    Main entry point for all requests
    Routes to salon business handler and WAITS for response
    
    Args:
        payload: Request payload with action and data
        background_tasks: FastAPI background tasks
    
    Returns:
        Response: Contains session_id, status, and message with actual result
    """
    try:
        from src.core.BusinessServiceManagement import business_service_cache
        
        # Get business service - initializes cache automatically if needed
        payload.operation_id = business_service_cache.get_operation_id(payload.business, payload.service_type)

        # Queue request to worker
        response = await check_and_route_business(
            payload.model_dump(),
            background_tasks
        )

        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


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
