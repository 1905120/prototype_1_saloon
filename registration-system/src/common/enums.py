"""
Enums for OperationType, Status, etc.
"""
from enum import Enum


class OperationType(Enum):
    """Operation types"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class PipelineStatus(Enum):
    """Pipeline execution status"""
    LOADED = "LOADED"
    CACHED = "CACHED"
    VALIDATED = "VALIDATED"
    PROCESSED = "PROCESSED"
    PERSISTED = "PERSISTED"
    FAILED = "FAILED"


class ApprovalStatus(Enum):
    """Customer/Client approval status"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MISSING_MANDATORY_FIELDS = "MISSING-MANDATORY-FIELDS"
