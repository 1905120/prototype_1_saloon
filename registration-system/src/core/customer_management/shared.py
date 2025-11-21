"""
Shared customer cache singleton management
"""
import json
import os
from typing import Dict, Any, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)

# Global registry of singleton caches keyed by path
_cache_registry: Dict[str, 'CustomerCache'] = {}
_registry_lock = Lock()


class CustomerCache:
    """Thread-safe customer cache for a specific business"""
    
    def __init__(self, path: str):
        """
        Initialize cache for a path
        
        Args:
            path: Path to customer metadata file
        """
        self.path = path
        self._data: Dict[str, Any] = {}
        
        # Use centralized lock manager
        from src.core.lock_manager import get_lock_manager
        from src.common.constants import ENABLE_LOCKING
        self.lock_manager = get_lock_manager(enable_locking=ENABLE_LOCKING)
        
        self._loaded = False
        
        # Load data immediately (eager load)
        self._load_from_file()
    
    def _load_from_file(self) -> None:
        """Load data from file"""
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r') as f:
                    self._data = json.load(f)
                logger.info(f"Loaded customer cache from {self.path}")
            else:
                self._data = {}
                logger.info(f"Customer cache file not found at {self.path}, starting with empty cache")
            self._loaded = True
        except Exception as e:
            logger.error(f"Failed to load customer cache from {self.path}: {str(e)}")
            self._data = {}
            self._loaded = True
    
    def _save_to_file(self) -> None:
        """Save data to file"""
        try:
            directory = os.path.dirname(self.path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            temp_path = f"{self.path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(self._data, f, indent=2)
            
            if os.path.exists(self.path):
                os.remove(self.path)
            os.rename(temp_path, self.path)
            
            logger.info(f"Saved customer cache to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save customer cache to {self.path}: {str(e)}")
            raise
    
    def read(self, key: str) -> Optional[Dict[str, Any]]:
        """Read value from cache (locking controlled by ENABLE_LOCKING)"""
        self.lock_manager.acquire_read_lock()
        try:
            return self._data.get(key)
        finally:
            self.lock_manager.release_read_lock()
    
    def write(self, key: str, value: Dict[str, Any]) -> None:
        """Write value to cache and save (locking controlled by ENABLE_LOCKING)"""
        self.lock_manager.acquire_write_lock()
        try:
            self._data[key] = value
            # Make a copy for file I/O outside lock
            data_copy = dict(self._data)
        finally:
            self.lock_manager.release_write_lock()
        self._save_to_file_unlocked(data_copy)
    
    def read_all(self) -> Dict[str, Any]:
        """Read entire cache (locking controlled by ENABLE_LOCKING)"""
        self.lock_manager.acquire_read_lock()
        try:
            return dict(self._data)
        finally:
            self.lock_manager.release_read_lock()
    
    def write_all(self, data: Dict[str, Any]) -> None:
        """Write entire cache and save (locking controlled by ENABLE_LOCKING)"""
        self.lock_manager.acquire_write_lock()
        try:
            self._data = dict(data)
            # Make a copy for file I/O outside lock
            data_copy = dict(self._data)
        finally:
            self.lock_manager.release_write_lock()
        self._save_to_file_unlocked(data_copy)
    
    def _save_to_file_unlocked(self, data: Dict[str, Any]) -> None:
        """Save data to file (called outside lock)"""
        try:
            directory = os.path.dirname(self.path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            temp_path = f"{self.path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            if os.path.exists(self.path):
                os.remove(self.path)
            os.rename(temp_path, self.path)
            
            logger.info(f"Saved customer cache to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save customer cache to {self.path}: {str(e)}")
            raise


def get_cache(path: str) -> CustomerCache:
    """
    Get or create singleton cache for a path
    
    Args:
        path: Path to customer metadata file
    
    Returns:
        CustomerCache singleton for this path
    """
    with _registry_lock:
        if path not in _cache_registry:
            _cache_registry[path] = CustomerCache(path)
            logger.info(f"Created new customer cache singleton for path: {path}")
        return _cache_registry[path]


def destroy_cache(path: str) -> None:
    """
    Destroy singleton cache for a path
    
    Args:
        path: Path to customer metadata file
    """
    with _registry_lock:
        if path in _cache_registry:
            del _cache_registry[path]
            logger.info(f"Destroyed customer cache singleton for path: {path}")
