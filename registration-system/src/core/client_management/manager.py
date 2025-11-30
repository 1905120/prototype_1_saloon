"""
Client management manager
"""
from typing import Dict, Any, Optional
from src.core.client_management import shared
import logging
import os
from datetime import datetime
import json
logger = logging.getLogger(__name__)

# Default customer metadata schema
DEFAULT_CLIENT_SCHEMA = {
    "metadata": {
        "total_clients": 0,
        "last_updated": datetime.now().isoformat(),
        "version": 1
    },
    "client": {}
}

class ClientManager:
    """Manager for client operations with singleton cache"""
    
    def __init__(self, business):
        """Initialize manager"""
        self._cache = None
        self._business = business
    
    def load_client_metadata(self, business: str) -> None:
        """
        Load client metadata for a business
        
        Args:
            business: Business identifier
        """
        # Derive path from business
        # Assuming metadata is stored in a standard location
        path = self._get_metadata_path(business)
        
        # Get singleton cache for this path
        self._cache = shared.get_cache(path)
        self._business = business
        
        logger.info(f"Loaded client metadata for business: {business}")
    
    def destroy_cache(self, business: str) -> None:
        """
        Destroy cache for a business
        
        Args:
            business: Business identifier
        """
        path = self._get_metadata_path(business)
        shared.destroy_cache(path)
        self._cache = None
        self._business = None
        
        logger.info(f"Destroyed client cache for business: {business}")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get specific client by key
        
        Args:
            key: Client key
        
        Returns:
            Client data or None
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_client_metadata first.")
        return self._cache.read(key)
    
    def put(self, key: str, value: Dict[str, Any]) -> None:
        """
        Put client data
        
        Args:
            key: Client key
            value: Client data
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_client_metadata first.")
        self._cache.write(key, value)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all clients
        
        Returns:
            All client data
        """
        # Get data from singleton cache
        data = self._cache.read_all()
        if data:
            return data

        schema_path = self._get_metaschema_path(self._business)
        # If data is empty and schema provided, create from schema
        if not data and schema_path:
            logger.info(f"Cache is empty, creating from schema: {schema_path}")
            data = self.create_default_schema_from_file(schema_path)
            # Write the initialized data back to cache
            self._cache.write_all(data)
        return data
    
    def _get_metaschema_path(Self, business):
        return f'DataModels/{business}/ClientSchema/Schema/meta-data.json'

    def create_default_schema_from_file(self, schema_file_path: str) -> Dict[str, Any]:

        try:
            if not os.path.exists(schema_file_path):
                logger.warning(f"Schema file not found: {schema_file_path}, using default")
                return DEFAULT_CLIENT_SCHEMA.copy()
            
            with open(schema_file_path, 'r') as f:
                schema = json.load(f)
            
            # Build default structure from schema
            default_data = {}
            
            if "properties" in schema:
                for prop_name, prop_schema in schema["properties"].items():
                    default_data[prop_name] = _get_default_value(prop_schema)
            
            logger.info(f"Created default schema from file: {schema_file_path}")
            return default_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {str(e)}")
            return DEFAULT_CLIENT_SCHEMA.copy()
        except Exception as e:
            logger.error(f"Error loading schema file: {str(e)}")
            return DEFAULT_CLIENT_SCHEMA.copy()

    def put_all(self, data: Dict[str, Any]) -> None:
        """
        Replace all client data
        
        Args:
            data: All client data
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_client_metadata first.")
        self._cache.write_all(data)
    
    def _get_metadata_path(self, business: str) -> str:
        """
        Derive metadata path from business
        
        Args:
            business: Business identifier
        
        Returns:
            Path to metadata file
        """
        # TODO: Implement business-to-path mapping
        # For now, assuming a standard structure
        return f"data/businesses/{business}/meta_data/client_metadata.json"

def _get_default_value(prop_schema: Dict[str, Any]) -> Any:
    """
    Get default value based on property schema type
    
    Args:
        prop_schema: Property schema definition
    
    Returns:
        Default value for the property type
    """
    prop_type = prop_schema.get("type")
    
    if prop_type == "object":
        if "properties" in prop_schema:
            obj = {}
            for key, value_schema in prop_schema["properties"].items():
                obj[key] = _get_default_value(value_schema)
            return obj
        return {}
    
    elif prop_type == "array":
        return []
    
    elif prop_type == "string":
        if prop_schema.get("format") == "date-time":
            return datetime.now().isoformat()
        return ""
    
    elif prop_type == "integer":
        return 0
    
    elif prop_type == "number":
        return 0.0
    
    elif prop_type == "boolean":
        return False
    
    else:
        return None