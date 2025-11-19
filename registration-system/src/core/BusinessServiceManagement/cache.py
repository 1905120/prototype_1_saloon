"""
Singleton cache for business service management available to all sessions
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from threading import Lock
from src.common.constants import BUSINESS_SERVICE_MODEL_SCHEMA_PATH, BUSINESS_SERVICE_MODEL_DATA_PATH

logger = logging.getLogger(__name__)


class BusinessServiceCache:
    """Singleton cache for business service models"""
    
    _instance = None
    _lock = Lock()
    _cache: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache = {}
        logger.info("BusinessServiceCache initialized")
    
    def load_business_service(self, business_name: str, schema_path: str) -> bool:
        """
        Load a business service model from JSON file into cache.
        
        Args:
            business_name: Name of the business
            schema_path: Path to the business service model JSON file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(schema_path, 'r') as f:
                data = json.load(f)
            self._cache[business_name] = data
            logger.info(f"Loaded business service model for {business_name}")
            return True
        except Exception as e:
            logger.error(f"Error loading business service model from {schema_path}: {str(e)}")
            return False
    
    def get_business_service(self, business_name: str) -> Dict[str, Any]:
        """
        Get a business service model from cache.
        Initializes cache if empty, then returns the business service data or empty structure.
        
        Args:
            business_name: Name of the business
        
        Returns:
            Business service model dict or empty structure if not found
        """
        # Initialize cache if empty
        if len(self._cache) == 0:
            self.initialize_cache(business_name=business_name)
        
        # Return cached data or empty structure
        if business_name in self._cache:
            return self._cache[business_name]
        
        # Return default empty structure if not in cache
        return {"business": {"name": business_name, "operations": {}}}
    
    def get_operation_id_by_service(self, cache_key: str, service_name: str) -> Optional[str]:
        """
        Get the operation ID for a specific service using cache key.
        
        Args:
            cache_key: Cache key (e.g., "business_service" - the filename without .json)
            service_name: Service name (e.g., "hair-cutting")
        
        Returns:
            Operation ID or None if not found
        """
        business_service = self.get_business_service(cache_key)
        if business_service:
            # Navigate through the structure: business -> (first key in business) -> service_name
            business_obj = business_service.get('business', {})
            # Get the first (and typically only) business name key
            if business_obj:
                # Get the first business in the object
                first_business = next(iter(business_obj.values()), {})
                return first_business.get(service_name)
        return None
    
    def get_operation_id(self, business_name: str, service_name: str) -> Optional[str]:
        """
        Get the operation ID for a specific business and service.
        Searches through all cached businesses to find the matching business name.
        
        Args:
            business_name: Name of the business (e.g., "salon")
            service_name: Service name (e.g., "hair-cutting")
        
        Returns:
            Operation ID or None if not found
        """
        if not self._cache:
            self.initialize_cache(business_name)
        # Search through all cached items
        for cache_key, cache_data in self._cache.items():
            business_obj = cache_data.get('business', {})
            # Check if this business name exists in the cache data
            if business_name in business_obj:
                services = business_obj[business_name]
                return services.get(service_name)
        return None
    
    def cache_all_businesses(self, businesses_config: Dict[str, str]) -> None:
        """
        Load multiple business service models into cache.
        
        Args:
            businesses_config: Dictionary mapping business names to schema paths
        """
        for business_name, schema_path in businesses_config.items():
            self.load_business_service(business_name, schema_path)
    
    def clear_cache(self) -> None:
        """Clear all cached business service models"""
        self._cache.clear()
        logger.info("BusinessServiceCache cleared")
    
    def get_all_businesses(self) -> Dict[str, Any]:
        """Get all cached business service models"""
        return self._cache.copy()
    
    def load_from_directory(self) -> Dict[str, bool]:
        """
        Load all business service models from BUSINESS_SERVICE_MODEL_DATA_PATH directory.
        Expects JSON files in the directory where filename is the business name.
        
        Returns:
            Dictionary mapping business names to load success status
        """
        results = {}
        dir_path = BUSINESS_SERVICE_MODEL_DATA_PATH
        
        if not os.path.isdir(dir_path):
            logger.error(f"Directory not found: {dir_path}")
            return results
        
        try:
            for filename in os.listdir(dir_path):
                if filename.endswith('.json'):
                    business_name = filename.replace('.json', '')
                    file_path = os.path.join(dir_path, filename)
                    success = self.load_business_service(business_name, file_path)
                    results[business_name] = success
            
            logger.info(f"Loaded {len([v for v in results.values() if v])} business services from {dir_path}")
        except Exception as e:
            logger.error(f"Error loading from directory {dir_path}: {str(e)}")
        
        return results
    
    def create_empty_structure(self, business_name: str) -> bool:
        """
        Create an empty business service structure from BUSINESS_SERVICE_MODEL_SCHEMA_PATH schema.
        Uses the schema to initialize an empty structure and cache it.
        
        Args:
            business_name: Name of the business
        
        Returns:
            True if structure created successfully, False otherwise
        """
        schema_path = BUSINESS_SERVICE_MODEL_SCHEMA_PATH
        
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Create empty structure based on schema properties
            empty_structure = {}
            properties = schema.get('properties', {})
            
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get('type')
                
                if prop_type == 'object':
                    empty_structure[prop_name] = {}
                elif prop_type == 'array':
                    empty_structure[prop_name] = []
                elif prop_type == 'string':
                    empty_structure[prop_name] = ""
                elif prop_type == 'number' or prop_type == 'integer':
                    empty_structure[prop_name] = 0
                elif prop_type == 'boolean':
                    empty_structure[prop_name] = False
                else:
                    empty_structure[prop_name] = None
            
            self._cache[business_name] = empty_structure
            logger.info(f"Created empty structure for {business_name} from schema")
            return True
        except Exception as e:
            logger.error(f"Error creating empty structure from schema {schema_path}: {str(e)}")
            return False
    
    def initialize_cache(self, business_name: Optional[str] = None) -> bool:
        """
        Initialize cache by loading from BUSINESS_SERVICE_MODEL_DATA_PATH or creating empty structure.
        If cache is not empty, does nothing.
        
        Args:
            business_name: Optional name of business for creating empty structure
        
        Returns:
            True always - either loads from directory, creates empty structure, or returns existing cache
        """
        # If cache already has data, skip initialization
        if len(self._cache) > 0:
            logger.info("Cache already populated, skipping initialization")
            return True
        
        # Try to load from directory first
        if os.path.isdir(BUSINESS_SERVICE_MODEL_DATA_PATH):
            results = self.load_from_directory()
            if any(results.values()):
                logger.info("Cache initialized from directory")
                return True
        
        # If directory loading failed, create empty structure from schema
        if business_name and os.path.isfile(BUSINESS_SERVICE_MODEL_SCHEMA_PATH):
            success = self.create_empty_structure(business_name)
            if success:
                logger.info("Cache initialized with empty structure from schema")
                return True
        
        # If schema file doesn't exist, create empty structure anyway
        if business_name:
            self._cache[business_name] = {"business": {"name": business_name, "operations": {}}}
            logger.info(f"Created default empty structure for {business_name}")
            return True
        
        logger.warning("Cache initialization: no business_name provided, cache remains empty")
        return True


# Singleton instance
business_service_cache = BusinessServiceCache()
