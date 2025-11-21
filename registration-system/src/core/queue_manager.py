"""
Thread-safe queue manager for request processing
Singleton pattern - initialized on first request
"""
import queue
from typing import Dict, Any, Optional
import logging
import threading
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# Global singleton instance
_queue_manager_instance = None
_initialization_lock = threading.Lock()


class QueueManager:
    """
    Manages thread-safe request queue for async processing
    Singleton pattern - initialized once globally
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, maxsize: int = 0):
        """Ensure only one instance exists"""
        if cls._instance is None:
            with _initialization_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, maxsize: int = 0):
        """
        Initialize queue manager (only once)
        
        Args:
            maxsize: Maximum queue size (0 = unlimited)
        """
        if QueueManager._initialized:
            return
        
        with _initialization_lock:
            if QueueManager._initialized:
                return
            
            self.request_queue = queue.Queue(maxsize=maxsize)
            self.results = {}  # Store results by session_id
            self.results_lock = threading.Lock()
            self.result_events = {}  # Asyncio events for each session
            self.status_tracker = {}  # Track status by session_id
            self.response_queue = {}  # Response queue - store final responses by session_id
            QueueManager._initialized = True
            logger.info(f"QueueManager initialized with maxsize={maxsize}")
    
    def put_to_queue(self, operation) -> None:
        """
        Add operation to queue
        
        Args:
            operation: Operation object (SessionData or dict) to queue
        
        Raises:
            RuntimeError: If queue is full
        """
        try:
            session_id = operation.session_id if hasattr(operation, 'session_id') else operation.get('session_id')
            self.request_queue.put(operation, block=True)
            logger.info(f"Operation queued: {session_id}")
        except queue.Full:
            logger.error("Request queue is full")
            raise RuntimeError("Request queue is full")
    
    def get_from_queue(self, timeout: Optional[float] = None):
        """
        Get operation from queue
        
        Args:
            timeout: Timeout in seconds (None = wait indefinitely)
        
        Returns:
            Operation from queue (SessionData or dict)
        
        Raises:
            queue.Empty: If queue is empty and timeout expires
        """
        try:
            operation = self.request_queue.get(block=True, timeout=timeout)
            session_id = operation.session_id if hasattr(operation, 'session_id') else operation.get('session_id')
            logger.info(f"Operation retrieved from queue: {session_id}")
            return operation
        except queue.Empty:
            logger.warning("Queue is empty")
            raise
    
    def mark_done(self) -> None:
        """Mark current task as done"""
        self.request_queue.task_done()
        logger.info("Task marked as done")
    
    def queue_size(self) -> int:
        """Get approximate queue size"""
        return self.request_queue.qsize()
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self.request_queue.empty()
    
    def store_result(self, session_id: str, result: Dict[str, Any]) -> None:
        """
        Store operation result by session_id and signal waiting coroutine
        
        Args:
            session_id: Session ID
            result: Operation result
        """
        with self.results_lock:
            self.results[session_id] = result
            logger.info(f"Result stored for session: {session_id}")
            
            # Signal the event if it exists
            if session_id in self.result_events:
                event = self.result_events[session_id]
                # Set event in the event loop
                try:
                    event.set()
                except RuntimeError:
                    logger.warning(f"Could not set event for session {session_id}")
    
    async def get_result_async(self, session_id: str) -> Dict[str, Any]:
        """
        Asynchronously wait for and retrieve operation result
        
        Args:
            session_id: Session ID
        
        Returns:
            Operation result
        """
        try:
            # Create event for this session in the current event loop
            event = asyncio.Event()
            
            with self.results_lock:
                self.result_events[session_id] = event
            
            # Wait for result
            await event.wait()
            
            # Retrieve result
            with self.results_lock:
                result = self.results.pop(session_id, {})
                logger.info(f"Result retrieved for session: {session_id}")
                return result
        finally:
            # Cleanup event
            with self.results_lock:
                self.result_events.pop(session_id, None)
    
    def set_status(self, session_id: str, status: str, message: str = "", progress: int = 0, error: str = None) -> None:
        """
        Set operation status
        
        Args:
            session_id: Session ID
            status: Status (QUEUED, PROCESSING, COMPLETED, FAILED)
            message: Status message
            progress: Progress percentage (0-100)
            error: Error details (if status is FAILED)
        """
        with self.results_lock:
            self.status_tracker[session_id] = {
                "status": status,
                "message": message,
                "progress": progress,
                "error": error,
                "updated_at": datetime.now().isoformat()
            }
            logger.info(f"Status set for session {session_id}: {status}")
    
    def get_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get operation status
        
        Args:
            session_id: Session ID
        
        Returns:
            Status information
        """
        with self.results_lock:
            status_info = self.status_tracker.get(session_id, {
                "status": "NOT_FOUND",
                "message": "Session not found",
                "progress": 0
            })
            logger.info(f"Status retrieved for session {session_id}: {status_info.get('status')}")
            return status_info
    
    def put_response(self, session_id: str, response: Dict[str, Any]) -> None:
        """
        Put response in response queue
        
        Args:
            session_id: Session ID
            response: Response data to store
        """
        with self.results_lock:
            self.response_queue[session_id] = {
                "session_id": session_id,
                "response": response,
                "stored_at": datetime.now().isoformat()
            }
            logger.info(f"Response stored in queue for session {session_id}")
    
    def get_response(self, session_id: str) -> Dict[str, Any]:
        """
        Get response from response queue
        
        Args:
            session_id: Session ID
        
        Returns:
            Response data or NOT_FOUND message
        """
        with self.results_lock:
            if session_id in self.response_queue:
                response_data = self.response_queue.pop(session_id)
                logger.info(f"Response retrieved from queue for session {session_id}")
                return response_data.get("response")
            else:
                logger.warning(f"Response not found in queue for session {session_id}")
                return {
                    "result": {
                        "response": {
                            "session_id": session_id
                        },
                        "status": "FAILED",
                        "message": "Response not yet available or already retrieved"
                    },
                    "err_details": {
                        "err_msg": "Response not found",
                        "err_type": "SYSTEM-PROCESS-ERR"
                    }
                }


def get_queue_manager(maxsize: int = 0) -> QueueManager:
    """
    Get or create singleton QueueManager instance
    
    Args:
        maxsize: Maximum queue size (only used on first call)
    
    Returns:
        QueueManager singleton instance
    """
    return QueueManager(maxsize=maxsize)
