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
