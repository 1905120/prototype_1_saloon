"""
System Cache Manager - Manages system-wide cache operations
Similar to MetadataManager but for system-level data
Thread-safe singleton pattern for use across multiple threads
"""
import logging
import os
import json
import threading
from typing import Dict, Any, Optional, List
from src.system_cache.cache import get_system_cache, SystemCache
from src.common.constants import SYSTEM_CACHE_PATH

logger = logging.getLogger(__name__)


class SystemCacheManager:
    """
    Manages system-wide cache operations
    Provides interface for reading/writing system cache data
    """
    
    def __init__(self, cache_path: str = SYSTEM_CACHE_PATH):
        """
        Initialize SystemCacheManager
        
        Args:
            cache_path: Path to system cache file
        """
        self.cache_path = cache_path
        self.cache = get_system_cache(cache_path)
        self.cache.load()
        logger.info(f"SystemCacheManager initialized with cache: {cache_path}")
    
    # ============ READ OPERATIONS ============
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from system cache
        
        Args:
            key: Key to retrieve (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Value from cache or default
        """
        try:
            self.cache.acquire_read_lock()
            
            # Support dot notation for nested keys
            if "." in key:
                keys = key.split(".")
                value = self.cache.data
                for k in keys:
                    if isinstance(value, dict):
                        value = value.get(k)
                    else:
                        return default
                return value if value is not None else default
            
            return self.cache.data.get(key, default)
        
        finally:
            self.cache.release_read_lock()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all system cache data"""
        try:
            self.cache.acquire_read_lock()
            return dict(self.cache.data)
        finally:
            self.cache.release_read_lock()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in system cache"""
        try:
            self.cache.acquire_read_lock()
            
            if "." in key:
                keys = key.split(".")
                value = self.cache.data
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return False
                return True
            
            return key in self.cache.data
        
        finally:
            self.cache.release_read_lock()
    
    # ============ WRITE OPERATIONS ============
    def set(self, key: str, value: Any) -> None:
        """
        Set value in system cache
        
        Args:
            key: Key to set (supports dot notation for nested keys)
            value: Value to set
        """
        try:
            self.cache.acquire_write_lock()
            
            # Support dot notation for nested keys
            if "." in key:
                keys = key.split(".")
                current = self.cache.data
                
                # Navigate/create nested structure
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                current[keys[-1]] = value
            else:
                self.cache.data[key] = value
            
            self.cache.save()
            logger.debug(f"Set system cache key: {key}")
        
        finally:
            self.cache.release_write_lock()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple values in system cache
        
        Args:
            updates: Dictionary of key-value pairs to update
        """
        try:
            self.cache.acquire_write_lock()
            
            for key, value in updates.items():
                if "." in key:
                    keys = key.split(".")
                    current = self.cache.data
                    
                    for k in keys[:-1]:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    
                    current[keys[-1]] = value
                else:
                    self.cache.data[key] = value
            
            self.cache.save()
            logger.debug(f"Updated system cache with {len(updates)} keys")
        
        finally:
            self.cache.release_write_lock()
    
    def delete(self, key: str) -> bool:
        """
        Delete key from system cache
        
        Args:
            key: Key to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            self.cache.acquire_write_lock()
            
            if "." in key:
                keys = key.split(".")
                current = self.cache.data
                
                # Navigate to parent
                for k in keys[:-1]:
                    if k in current and isinstance(current[k], dict):
                        current = current[k]
                    else:
                        return False
                
                if keys[-1] in current:
                    del current[keys[-1]]
                    self.cache.save()
                    return True
                return False
            
            if key in self.cache.data:
                del self.cache.data[key]
                self.cache.save()
                return True
            
            return False
        
        finally:
            self.cache.release_write_lock()
    
    def clear(self) -> None:
        """Clear all system cache data"""
        try:
            self.cache.acquire_write_lock()
            self.cache.data = {}
            self.cache.save()
            logger.info("Cleared all system cache data")
        
        finally:
            self.cache.release_write_lock()
    
    def load_file(self, key_name: str, file_path: str) -> Any:
        """
        Load data from file and cache it with given key name
        
        Args:
            key_name: Key name to store the data under
            file_path: Path to the file to load
            
        Returns:
            Loaded data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        try:
            import json
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file
            with open(file_path, 'r') as f:
                content = f.read().strip()
            
            if not content:
                logger.warning(f"File is empty: {file_path}")
                data = {}
            else:
                # Try to parse as JSON
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # If not JSON, store as raw text
                    logger.warning(f"File is not valid JSON, storing as text: {file_path}")
                    data = content
            
            # Cache the data
            self.set(key_name, data)
            logger.info(f"Loaded and cached file {file_path} with key: {key_name}")
            
            return data
        
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise
    
    # ============ UTILITY OPERATIONS ============
    def set_dict_value(self, key: str, dict_key: str, value: Any) -> None:
        """
        Set value in a dictionary within system cache
        
        Args:
            key: Key of the dictionary
            dict_key: Key within the dictionary
            value: Value to set
        """
        try:
            self.cache.acquire_write_lock()
            
            if key not in self.cache.data:
                self.cache.data[key] = {}
            
            if isinstance(self.cache.data[key], dict):
                self.cache.data[key][dict_key] = value
                self.cache.save()
            else:
                logger.warning(f"Key {key} is not a dictionary")
        
        finally:
            self.cache.release_write_lock()
    
    def get_dict_value(self, key: str, dict_key: str, default: Any = None) -> Any:
        """
        Get value from a dictionary in system cache
        
        Args:
            key: Key of the dictionary
            dict_key: Key within the dictionary
            default: Default value if not found
            
        Returns:
            Value from dictionary or default
        """
        try:
            self.cache.acquire_read_lock()
            
            if key in self.cache.data and isinstance(self.cache.data[key], dict):
                return self.cache.data[key].get(dict_key, default)
            
            return default
        
        finally:
            self.cache.release_read_lock()
    
    def delete_dict_value(self, key: str, dict_key: str) -> bool:
        """
        Delete value from a dictionary in system cache
        
        Args:
            key: Key of the dictionary
            dict_key: Key within the dictionary
            
        Returns:
            True if deleted, False if not found
        """
        try:
            self.cache.acquire_write_lock()
            
            if key in self.cache.data and isinstance(self.cache.data[key], dict):
                if dict_key in self.cache.data[key]:
                    del self.cache.data[key][dict_key]
                    self.cache.save()
                    return True
            
            return False
        
        finally:
            self.cache.release_write_lock()
    
    def get_dict(self, key: str, default: Optional[Dict] = None) -> Dict:
        """
        Get entire dictionary from system cache
        
        Args:
            key: Key of the dictionary
            default: Default dictionary if not found
            
        Returns:
            Dictionary or default
        """
        try:
            self.cache.acquire_read_lock()
            
            if key in self.cache.data and isinstance(self.cache.data[key], dict):
                return dict(self.cache.data[key])
            
            return default or {}
        
        finally:
            self.cache.release_read_lock()
    
    def update_dict(self, key: str, updates: Dict[str, Any]) -> None:
        """
        Update multiple values in a dictionary within system cache
        
        Args:
            key: Key of the dictionary
            updates: Dictionary of key-value pairs to update
        """
        try:
            self.cache.acquire_write_lock()
            
            if key not in self.cache.data:
                self.cache.data[key] = {}
            
            if isinstance(self.cache.data[key], dict):
                self.cache.data[key].update(updates)
                self.cache.save()
            else:
                logger.warning(f"Key {key} is not a dictionary")
        
        finally:
            self.cache.release_write_lock()
    
    def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment numeric value in system cache
        
        Args:
            key: Key to increment
            amount: Amount to increment by
            
        Returns:
            New value
        """
        try:
            self.cache.acquire_write_lock()
            
            current = self.cache.data.get(key, 0)
            new_value = current + amount
            self.cache.data[key] = new_value
            self.cache.save()
            
            return new_value
        
        finally:
            self.cache.release_write_lock()


# Global system cache manager instance and lock
_system_cache_manager = None
_manager_lock = threading.Lock()


def get_system_cache_manager(cache_path: str = SYSTEM_CACHE_PATH) -> SystemCacheManager:
    """
    Get or create global SystemCacheManager instance (Thread-safe singleton)
    
    This function ensures only one SystemCacheManager instance exists
    and can be safely called from any thread.
    
    Args:
        cache_path: Path to system cache file
        
    Returns:
        SystemCacheManager instance (singleton)
    """
    global _system_cache_manager, _manager_lock
    
    # Double-checked locking pattern for thread safety
    if _system_cache_manager is None:
        with _manager_lock:
            # Check again inside lock to prevent race condition
            if _system_cache_manager is None:
                _system_cache_manager = SystemCacheManager(cache_path)
                logger.info(f"Created singleton SystemCacheManager instance")
    
    return _system_cache_manager
