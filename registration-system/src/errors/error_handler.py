"""
Error handling logic
"""
from .exceptions import (
    PipelineException,
    ValidationError,
    SessionNotFoundError,
    StorageError,
    ProcessingError,
    CacheError
)


class ErrorHandler:
    """Centralized error handling"""

    @staticmethod
    def raise_datapipeline_error(message: str) -> None:
        """Raise validation error"""
        raise PipelineException(message)
    
    @staticmethod
    def raise_validation_error(message: str) -> None:
        """Raise validation error"""
        raise ValidationError(message)
    
    @staticmethod
    def raise_session_not_found(session_id: str) -> None:
        """Raise session not found error"""
        raise SessionNotFoundError(f"Session {session_id} not found")
    
    @staticmethod
    def raise_storage_error(message: str) -> None:
        """Raise storage error"""
        raise StorageError(message)
    
    @staticmethod
    def raise_processing_error(message: str) -> None:
        """Raise processing error"""
        raise ProcessingError(message)
    
    @staticmethod
    def raise_cache_error(message: str) -> None:
        """Raise cache error"""
        raise CacheError(message)


# ============ ERROR STORAGE CACHE ============
import threading
from datetime import datetime
from typing import Dict, Any, Optional


class ErrorStore:
    """Error storage cache - stores errors by phone number (default key)"""
    
    store_error: Dict[str, Dict[str, Any]] = {}
    _cache_lock = threading.Lock()
    
    @classmethod
    def store(cls, key: str, error_msg: str, error_type: str = "SYSTEM-PROCESS-ERR", addon: str = "") -> None:
        """
        Store error by key (default: phone number)
        
        Args:
            key: Key identifier (phone number by default)
            error_msg: Error message
            error_type: Error type (BUSSINESS-PROCESS-ERR or SYSTEM-PROCESS-ERR)
            addon: Additional error information
        """
        with cls._cache_lock:
            cls.store_error[key] = {
                "error_msg": error_msg + addon if addon else error_msg,
                "error_type": error_type,
                "timestamp": datetime.now().isoformat()
            }
    
    @classmethod
    def get(cls, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve error by key (default: phone number)
        
        Args:
            key: Key identifier (phone number by default)
        
        Returns:
            Error details or None if not found
        """
        with cls._cache_lock:
            return cls.store_error.get(key)
    
    @classmethod
    def remove(cls, key: str) -> None:
        """
        Remove error by key (default: phone number)
        
        Args:
            key: Key identifier (phone number by default)
        """
        with cls._cache_lock:
            cls.store_error.pop(key, None)
    
    @classmethod
    def clear_all_errors(cls) -> None:
        """Clear all stored errors"""
        with cls._cache_lock:
            cls.store_error.clear()
    
    @classmethod
    def get_all_errors(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all stored errors
        
        Returns:
            Dictionary of all stored errors
        """
        with cls._cache_lock:
            return cls.store_error.copy()


# ============ ERROR RESPONSE BUILDER ============
class ErrorResponse:
    """Build standardized error responses"""
    
    @staticmethod
    def build(error_type: str, error_msg: str, message: str, response_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Build standardized error response
        
        Args:
            error_type: Error type (BUSSINESS-PROCESS-ERR or SYSTEM-PROCESS-ERR)
            error_msg: Technical error message
            message: User-friendly message
            response_data: Optional response data to include
        
        Returns:
            Standardized error response dictionary
        """
        return {
            "result": {
                "response": response_data or {},
                "status": "FAILED",
                "message": message
            },
            "err_details": {
                "err_msg": error_msg,
                "err_type": error_type
            }
        }
