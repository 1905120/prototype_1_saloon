"""
Centralized lock manager - Controls all read/write locking across the system
Can be toggled via ENABLE_LOCKING constant
"""
import threading
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LockManager:
    """Centralized lock management with toggle capability"""
    
    def __init__(self, enable_locking: bool = True):
        """
        Initialize lock manager
        
        Args:
            enable_locking: Whether to enable locking (default: True)
        """
        self.enable_locking = enable_locking
        self.lock = threading.Lock()
        logger.info(f"LockManager initialized - Locking {'ENABLED' if enable_locking else 'DISABLED'}")
    
    def set_locking(self, enable: bool) -> None:
        """
        Enable or disable locking globally
        
        Args:
            enable: True to enable locking, False to disable
        """
        self.enable_locking = enable
        logger.info(f"Locking {'ENABLED' if enable else 'DISABLED'}")
    
    def acquire_read_lock(self) -> None:
        """Acquire read lock (if locking enabled)"""
        if self.enable_locking:
            self.lock.acquire()
    
    def release_read_lock(self) -> None:
        """Release read lock (if locking enabled)"""
        if self.enable_locking:
            self.lock.release()
    
    def acquire_write_lock(self) -> None:
        """Acquire write lock (if locking enabled)"""
        if self.enable_locking:
            self.lock.acquire()
    
    def release_write_lock(self) -> None:
        """Release write lock (if locking enabled)"""
        if self.enable_locking:
            self.lock.release()
    
    def with_read_lock(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with read lock
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        """
        if self.enable_locking:
            self.acquire_read_lock()
        try:
            return func(*args, **kwargs)
        finally:
            if self.enable_locking:
                self.release_read_lock()
    
    def with_write_lock(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with write lock
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        """
        if self.enable_locking:
            self.acquire_write_lock()
        try:
            return func(*args, **kwargs)
        finally:
            if self.enable_locking:
                self.release_write_lock()


# Global singleton instance
_lock_manager: Optional[LockManager] = None


def get_lock_manager(enable_locking: bool = True) -> LockManager:
    """
    Get or create global lock manager instance
    
    Args:
        enable_locking: Whether to enable locking
    
    Returns:
        Global LockManager instance
    """
    global _lock_manager
    
    if _lock_manager is None:
        _lock_manager = LockManager(enable_locking=enable_locking)
    
    return _lock_manager


def set_global_locking(enable: bool) -> None:
    """
    Set global locking state
    
    Args:
        enable: True to enable, False to disable
    """
    manager = get_lock_manager()
    manager.set_locking(enable)
