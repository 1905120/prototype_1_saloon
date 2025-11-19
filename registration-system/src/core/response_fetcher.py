"""
Response fetcher - handles waiting for and caching responses
Singleton pattern - initialized once globally
"""
import threading
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Global singleton instance
_response_fetcher_instance = None
_initialization_lock = threading.Lock()


class ResponseFetcher:
    """
    Manages response caching and retrieval
    Singleton pattern - initialized once globally
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Ensure only one instance exists"""
        if cls._instance is None:
            with _initialization_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize response fetcher (only once)
        """
        if ResponseFetcher._initialized:
            return
        
        with _initialization_lock:
            if ResponseFetcher._initialized:
                return
            
            self.response_cache = {}  # Cache responses by session_id
            self.cache_lock = threading.Lock()
            self.response_events = {}  # Threading events for each session
            self.is_running = False
            ResponseFetcher._initialized = True
            logger.info("ResponseFetcher initialized")
    
    def start(self) -> None:
        """Start the response fetcher"""
        self.is_running = True
        logger.info("ResponseFetcher started")
    
    def stop(self) -> None:
        """Stop the response fetcher"""
        self.is_running = False
        logger.info("ResponseFetcher stopped")
    
    def cache_response(self, session_id: str, response: Dict[str, Any]) -> None:
        """
        Cache a response and signal waiting threads
        
        Args:
            session_id: Session ID
            response: Response data to cache
        """
        with self.cache_lock:
            self.response_cache[session_id] = {
                "response": response,
                "cached_at": datetime.now().isoformat()
            }
            logger.info(f"Response cached for session {session_id}")
            
            # Signal the event if it exists
            if session_id in self.response_events:
                event = self.response_events[session_id]
                event.set()
                logger.info(f"Signaled waiting thread for session {session_id}")
    
    def put_response(self, session_id: str, response: Dict[str, Any]) -> None:
        """
        Put response in cache (alias for cache_response)
        
        Args:
            session_id: Session ID
            response: Response data to cache
        """
        self.cache_response(session_id, response)
    
    def get_response(self, session_id: str, timeout: float = 60) -> Dict[str, Any]:
        """
        Get response with timeout (blocking call)
        
        Args:
            session_id: Session ID
            timeout: Timeout in seconds
        
        Returns:
            Response data
        """
        try:
            # Create event for this session
            event = threading.Event()
            
            with self.cache_lock:
                self.response_events[session_id] = event
                
                # Check if response already cached
                if session_id in self.response_cache:
                    cached_data = self.response_cache.pop(session_id)
                    logger.info(f"Response retrieved for session {session_id}")
                    return cached_data["response"]
            
            # Wait for response with timeout
            if event.wait(timeout=timeout):
                with self.cache_lock:
                    if session_id in self.response_cache:
                        cached_data = self.response_cache.pop(session_id)
                        logger.info(f"Response retrieved for session {session_id}")
                        return cached_data["response"]
            
            # Timeout occurred
            logger.warning(f"Response timeout for session {session_id} after {timeout}s")
            return {
                "session_id": session_id,
                "status": "TIMEOUT",
                "message": f"Response not received within {timeout} seconds"
            }
        
        finally:
            # Cleanup event
            with self.cache_lock:
                self.response_events.pop(session_id, None)
    
    def clear_cache(self, session_id: str) -> None:
        """
        Clear cached response for a session
        
        Args:
            session_id: Session ID
        """
        with self.cache_lock:
            if session_id in self.response_cache:
                del self.response_cache[session_id]
                logger.info(f"Cache cleared for session {session_id}")
    
    def get_cache_size(self) -> int:
        """Get number of cached responses"""
        with self.cache_lock:
            return len(self.response_cache)


def get_response_fetcher() -> ResponseFetcher:
    """
    Get or create singleton ResponseFetcher instance
    
    Returns:
        ResponseFetcher singleton instance
    """
    return ResponseFetcher()
