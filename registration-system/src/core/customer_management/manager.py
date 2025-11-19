"""
Customer management manager
"""
from typing import Dict, Any, Optional
from src.core.customer_management import shared
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Default customer metadata schema
DEFAULT_CUSTOMER_SCHEMA = {
    "metadata": {
        "total_customers": 0,
        "last_updated": datetime.now().isoformat(),
        "version": 1
    },
    "customers": {}
}


def create_default_schema_from_file(schema_file_path: str) -> Dict[str, Any]:
    """
    Create default schema structure from a JSON schema file
    
    Args:
        schema_file_path: Path to JSON schema file
    
    Returns:
        Default schema structure
    
    Raises:
        FileNotFoundError: If schema file not found
        json.JSONDecodeError: If schema file is invalid JSON
    """
    try:
        if not os.path.exists(schema_file_path):
            logger.warning(f"Schema file not found: {schema_file_path}, using default")
            return DEFAULT_CUSTOMER_SCHEMA.copy()
        
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
        return DEFAULT_CUSTOMER_SCHEMA.copy()
    except Exception as e:
        logger.error(f"Error loading schema file: {str(e)}")
        return DEFAULT_CUSTOMER_SCHEMA.copy()


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


class CustomerManager:
    """Manager for customer operations with singleton cache"""
    
    def __init__(self, business):
        """Initialize manager"""
        self._cache = None
        self._business = business
        
    def load_customer_metadata(self) -> None:
        """
        Load customer metadata for a business
        
        Args:
            business: Business identifier
        """
        # Derive path from business
        # Assuming metadata is stored in a standard location
        path = self._get_metadata_path(self._business)
        
        # Get singleton cache for this path
        self._cache = shared.get_cache(path)
        if not self._cache: 
            self._cache = self.get_all()
        self._business = self._business
        
        logger.info(f"Loaded customer metadata for business: {self._business}")
    
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
        
        logger.info(f"Destroyed customer cache for business: {business}")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get specific customer by key
        
        Args:
            key: Customer key
        
        Returns:
            Customer data or None
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_customer_metadata first.")
        return self._cache.read(key)
    
    def put(self, key: str, value: Dict[str, Any]) -> None:
        """
        Put customer data
        
        Args:
            key: Customer key
            value: Customer data
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_customer_metadata first.")
        self._cache.write(key, value)
    
    def get_all(self, schema_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all customers from singleton cache
        If cache is empty and schema_path provided, create default structure from schema
        
        Args:
            schema_path: Optional path to JSON schema file for initialization
        
        Returns:
            All customer data
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_customer_metadata first.")
        
        # Get data from singleton cache
        data = self._cache.read_all()
        schema_path = self._get_metaschema_path(self._business)
        # If data is empty and schema provided, create from schema
        if not data and schema_path:
            logger.info(f"Cache is empty, creating from schema: {schema_path}")
            data = create_default_schema_from_file(schema_path)
            # Write the initialized data back to cache
            self._cache.write_all(data)
        
        return data
    
    def put_all(self, data: Dict[str, Any]) -> None:
        """
        Replace all customer data
        
        Args:
            data: All customer data
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_customer_metadata first.")
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
        return f"data/businesses/{business}/meta_data/customer_meta_data.json"
    
    def _get_metaschema_path(self, business: str) -> str:
        """
        Derive metadata path from business
        
        Args:
            business: Business identifier
        
        Returns:
            Path to metadata file
        """
        # TODO: Implement business-to-path mapping
        # For now, assuming a standard structure
        return f'DataModels/{business}/CustomerSchema/Schema/meta-data.json'
    
    def validate_meta_data_schema(self, data: Dict[str, Any]) -> bool:
        """
        Validate customer metadata against schema
        
        Args:
            data: Customer metadata to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required top-level keys
            if "metadata" not in data or "customers" not in data:
                logger.error("Missing required keys: metadata or customers")
                return False
            
            # Validate metadata
            metadata = data.get("metadata", {})
            if not isinstance(metadata, dict):
                logger.error("metadata must be an object")
                return False
            
            required_metadata_keys = ["total_customers", "last_updated", "version"]
            for key in required_metadata_keys:
                if key not in metadata:
                    logger.error(f"Missing required metadata key: {key}")
                    return False
            
            # Validate customers object
            customers = data.get("customers", {})
            if not isinstance(customers, dict):
                logger.error("customers must be an object")
                return False
            
            # Validate each customer entry
            for phone, customer_data in customers.items():
                if not isinstance(customer_data, dict):
                    logger.error(f"Customer data for {phone} must be an object")
                    return False
                
                required_customer_keys = ["client_id", "latest_version", "versions"]
                for key in required_customer_keys:
                    if key not in customer_data:
                        logger.error(f"Missing required customer key: {key}")
                        return False
            
            logger.info("Schema validation passed")
            return True
        
        except Exception as e:
            logger.error(f"Schema validation error: {str(e)}")
            return False
    
    def ensure_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure data conforms to schema, fill defaults if needed
        
        Args:
            data: Customer metadata
        
        Returns:
            Data conforming to schema
        """
        if not data:
            return DEFAULT_CUSTOMER_SCHEMA.copy()
        
        # Ensure metadata exists
        if "metadata" not in data:
            data["metadata"] = DEFAULT_CUSTOMER_SCHEMA["metadata"].copy()
        
        # Ensure customers exists
        if "customers" not in data:
            data["customers"] = {}
        
        # Update last_updated
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        return data
    
    def remove_entry(self, key: str) -> bool:
        """
        Remove a customer entry from cache by key
        
        Args:
            key: Customer key to remove
        
        Returns:
            True if entry was removed, False if key not found
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_customer_metadata first.")
        
        try:
            # Get all data
            data = self._cache.read_all()
            
            # Check if key exists in customers
            if "customer" in data and key in data["customer"]:
                # Remove the entry
                del data["customer"][key]

                if "metadata" in data and "total_customers" in data["metadata"]:
                    data["metadata"]["total_customers"] -= 1

                # Write back to cache
                self._cache.write_all(data)
                
                logger.info(f"Removed customer entry: {key}")
                return True
            else:
                logger.warning(f"Customer key not found: {key}")
                return False
        
        except Exception as e:
            logger.error(f"Error removing entry {key}: {str(e)}")
            return False
    
    def remove_customer_entry(self, phone: str) -> bool:
        """
        Remove latest version entry for a customer by phone number
        If latest_version is 1, do nothing
        If latest_version > 1, remove the latest version from versions array
        
        Args:
            phone: Customer phone number
        
        Returns:
            True if entry was removed, False if phone not found or version is 1
        """
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_customer_metadata first.")
        
        try:
            # Get all data
            data = self._cache.read_all()
            
            # Check if phone exists in customer data
            if "customer" not in data or phone not in data["customer"]:
                logger.warning(f"Customer phone not found: {phone}")
                return False
            
            customer_data = data["customer"][phone]
            latest_version = customer_data.get("latest_latest_version", 1)
            
            # If latest version is 1, do nothing
            if latest_version <= 1:
                logger.info(f"Customer {phone} has version 1, no removal needed")
                return False
            
            # Find and remove the latest version entry from versions array
            versions = customer_data.get("versions", [])
            
            # Find the entry with the latest version
            version_to_remove = None
            for i, version_entry in enumerate(versions):
                if isinstance(version_entry, dict) and latest_version in version_entry:
                    version_to_remove = i
                    break
            
            if version_to_remove is not None:
                # Remove the latest version entry
                versions.pop(version_to_remove)
                
                # Update latest_latest_version to previous version
                customer_data["latest_latest_version"] = latest_version - 1
                customer_data["versions"] = versions
                
                # Write back to cache
                self._cache.write_all(data)
                
                logger.info(f"Removed version {latest_version} for customer {phone}")
                return True
            else:
                logger.warning(f"Could not find version {latest_version} in versions array for {phone}")
                return False
        
        except Exception as e:
            logger.error(f"Error removing customer entry for {phone}: {str(e)}")
            return False
