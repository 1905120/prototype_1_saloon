"""
Worker thread for processing queued operations
"""
import threading
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Worker:
    """Worker thread that processes operations from queue"""
    
    def __init__(self, worker_id: int = 0):
        """
        Initialize worker
        
        Args:
            worker_id: Worker identifier
        """
        self.worker_id = worker_id
        self.thread = None
        self.running = False
    
    def start(self) -> None:
        """Start worker thread"""
        if self.running:
            logger.warning(f"Worker {self.worker_id} already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        logger.info(f"Worker {self.worker_id} thread started")
    
    def stop(self) -> None:
        """Stop worker thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0)
        logger.info(f"Worker {self.worker_id} thread stopped")
    
    def _process_loop(self) -> None:
        """Main worker loop - continuously process queue"""
        from src.core.queue_manager import get_queue_manager
        import queue
        import asyncio
        
        queue_manager = get_queue_manager()
        
        logger.info(f"Worker {self.worker_id} loop started")
        
        while self.running:
            try:
                # Get operation from queue (wait indefinitely)
                operation = queue_manager.get_from_queue(timeout=None)
                
                # Process operation asynchronously
                asyncio.run(self._process_operation(operation))
                
                # Mark task as done
                queue_manager.mark_done()
                
            except queue.Empty:
                # Queue is empty, continue waiting
                continue
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {str(e)}", exc_info=True)
                try:
                    queue_manager.mark_done()
                except Exception as mark_error:
                    logger.error(f"Worker {self.worker_id} error marking task done: {str(mark_error)}")
    
    async def _process_operation(self, operation) -> None:
        """
        Process a single operation
        
        Args:
            operation: Operation from queue (SessionData object)
        """
        try:
            # Handle both SessionData objects and dicts
            if hasattr(operation, 'session_id'):
                # SessionData object
                session_id = operation.session_id
                operation_type = operation.operation_type
            else:
                # Dict
                session_id = operation.get("session_id")
                operation_type = operation.get("operation_type")
            
            logger.info(f"Worker {self.worker_id} processing operation: {session_id}")
            logger.info(f"Worker {self.worker_id} operation type: {operation_type}")
            
            # Store result for session manager to retrieve
            from src.core.queue_manager import get_queue_manager
            from src.core.pipeline import DataPipeline
            queue_manager = get_queue_manager()
            
            # Update status to PROCESSING
            queue_manager.set_status(
                session_id,
                "PROCESSING",
                f"Processing {operation_type}",
                25
            )
            
            # Await the async task
            process = DataPipeline(operation)
            result = await process.template_flow(operation.operation)
            logger.info(f"Worker {self.worker_id} task result: {result}")

            # Update status to COMPLETED
            queue_manager.set_status(
                session_id,
                "COMPLETED",
                f"Operation {operation_type} completed successfully",
                100
            )

            # result = {
            #     "session_id": session_id,
            #     "status": "SUCCESS",
            #     "message": f"Operation {operation_type} processed",
            #     "data": task_result
            # }
            
            logger.info(f"Worker {self.worker_id} operation completed: {session_id}")
            
            # Put response in response queue and notify session manager
            queue_manager.put_response(session_id, result)
            
            # Notify session manager
            from src.core.session import SessionManager
            SessionManager.put_response(session_id, result)
            
            queue_manager.store_result(session_id, result)
            
        except Exception as e:
            logger.error(f"Error in _process_operation: {str(e)}", exc_info=True)
            
            # Update status to FAILED with error details
            from src.core.queue_manager import get_queue_manager
            queue_manager = get_queue_manager()
            
            if hasattr(operation, 'session_id'):
                session_id = operation.session_id
                operation_type = operation.operation_type
            else:
                session_id = operation.get("session_id")
                operation_type = operation.get("operation_type")
            
            queue_manager.set_status(
                session_id,
                "FAILED",
                f"Error processing {operation_type}",
                0,
                error=str(e)
            )
            
            # Put error response in response queue and notify session manager
            error_response = {
                "session_id": session_id,
                "status": "FAILED",
                "message": f"Error processing {operation_type}",
                "error": str(e),
                "data": None
            }
            queue_manager.put_response(session_id, error_response)
            
            # Notify session manager
            from src.core.session import SessionManager
            SessionManager.put_response(session_id, error_response)


# Global worker instance
_worker_instance = None
_worker_lock = threading.Lock()


def get_worker() -> Worker:
    """Get or create global worker instance"""
    global _worker_instance
    
    if _worker_instance is None:
        with _worker_lock:
            if _worker_instance is None:
                _worker_instance = Worker()
    
    return _worker_instance


def stop_workers():
    try:
        from src.core.worker_pool import get_worker_pool
        worker_pool = get_worker_pool()
        worker_pool.stop()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        raise
    return