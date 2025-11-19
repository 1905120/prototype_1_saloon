"""
Custom exceptions
"""


class PipelineException(Exception):
    """Base exception for pipeline errors"""
    pass


class ValidationError(PipelineException):
    """Raised when validation fails"""
    pass


class SessionNotFoundError(PipelineException):
    """Raised when session is not found"""
    pass


class StorageError(PipelineException):
    """Raised when storage operation fails"""
    pass


class ProcessingError(PipelineException):
    """Raised when processing fails"""
    pass


class CacheError(PipelineException):
    """Raised when cache operation fails"""
    pass
