"""
System Cache - Singleton data structure holder for system-wide data
Similar to UniversalCache but for system-level operations
"""
import json
import threading
import os
from typing import Dict, Any, Optional
from src.errors.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)

# Global singleton instances
_cache_instances = {}
_cache_lock = threading.Lock()


def get_system_cache(cache_path: str, schema_path: Optional[str] = None) -> 'SystemCache':
    """
    Get or create a singleton SystemCache instance for the given path
    
    Args:
        cache_path: Path to system cache file (data path)
        schema_path: Path to JSON schema file (optional)
    
    Returns:
        Singleton SystemCache instance
    """
    global _cache_instances, _cache_lock
    
    with _cache_lock:
        # Return existing instance if already created
        if cache_path in _cache_instances:
            logger.debug(f"Returning existing system cache instance for: {cache_path}")
            return _cache_instances[cache_path]
        
        # Create new singleton instance
        logger.info(f"Creating new singleton system cache instance for: {cache_path}")
        instance = SystemCache(cache_path, schema_path=schema_path)
        _cache_instances[cache_path] = instance
        return instance


class SystemCache:
    """
    System Cache - Singleton data structure holder
    Stores system-wide metadata in memory with file persistence
    Similar to UniversalCache but for system-level operations
    """
    
    def __init__(self, cache_path: str, schema_path: Optional[str] = None):
        """
        Initialize system cache
        
        Args:
            cache_path: Path to cache file (system_cache.json)
            schema_path: Path to JSON schema file (optional)
        """
        self.cache_path = cache_path
        self.schema_path = schema_path
        self.data = {}  # In-memory data store
        self.is_loaded = False
        
        # Use centralized lock manager
        from src.core.lock_manager import get_lock_manager
        from src.common.constants import ENABLE_LOCKING
        self.lock_manager = get_lock_manager(enable_locking=ENABLE_LOCKING)
        
        logger.info(f"SystemCache initialized: {cache_path} (schema: {schema_path})")
    
    def load(self) -> None:
        """Load data from file or initialize from schema if empty (called by SystemCacheManager)"""
        try:
            if not os.path.exists(self.cache_path):
                logger.warning(f"System cache file not found: {self.cache_path}")
                
                # If schema path provided, create default structure from schema
                if self.schema_path:
                    logger.info(f"Initializing from schema: {self.schema_path}")
                    self.data = self._create_from_schema()
                    # Save the initialized data
                    self.save()
                else:
                    self.data = {}
            else:
                with open(self.cache_path, 'r') as f:
                    content = f.read().strip()
                
                # If file is empty and schema provided, initialize from schema
                if not content and self.schema_path:
                    logger.info(f"System cache file is empty, initializing from schema: {self.schema_path}")
                    self.data = self._create_from_schema()
                    self.save()
                elif content:
                    self.data = json.loads(content)
                    logger.info(f"Loaded system cache from {self.cache_path}")
                else:
                    self.data = {}
                    logger.info(f"System cache file is empty and no schema provided")
            
            self.is_loaded = True
        except Exception as e:
            logger.error(f"Failed to load system cache: {str(e)}")
            raise
    
    def _create_from_schema(self) -> Dict[str, Any]:
        """
        Create default data structure from schema file
        
        Returns:
            Default data structure based on schema
        """
        try:
            if not self.schema_path or not os.path.exists(self.schema_path):
                logger.warning(f"Schema file not found: {self.schema_path}")
                return {}
            
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            
            # Use customer manager's schema creation function
            from src.core.customer_management.manager import _get_default_value
            
            default_data = {}
            if "properties" in schema:
                for prop_name, prop_schema in schema["properties"].items():
                    default_data[prop_name] = _get_default_value(prop_schema)
            
            logger.info(f"Created default structure from schema: {self.schema_path}")
            return default_data
        
        except Exception as e:
            logger.error(f"Failed to create from schema: {str(e)}")
            return {}
    
    def save(self) -> None:
        """Save data to file (called by SystemCacheManager)"""
        try:
            directory = os.path.dirname(self.cache_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Atomic write
            temp_path = f"{self.cache_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            
            if os.path.exists(self.cache_path):
                os.remove(self.cache_path)
            os.rename(temp_path, self.cache_path)
            
            logger.info(f"Saved system cache to {self.cache_path}")
        except Exception as e:
            logger.error(f"Failed to save system cache: {str(e)}")
            raise
    
    # ============ LOCK OPERATIONS ============
    def acquire_read_lock(self) -> None:
        """Acquire read lock (controlled by ENABLE_LOCKING)"""
        self.lock_manager.acquire_read_lock()
    
    def release_read_lock(self) -> None:
        """Release read lock (controlled by ENABLE_LOCKING)"""
        self.lock_manager.release_read_lock()
    
    def acquire_write_lock(self) -> None:
        """Acquire write lock (controlled by ENABLE_LOCKING)"""
        self.lock_manager.acquire_write_lock()
    
    def release_write_lock(self) -> None:
        """Release write lock (controlled by ENABLE_LOCKING)"""
        self.lock_manager.release_write_lock()
