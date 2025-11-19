"""
Metadata manager for handling version tracking and business operations
All cache operations go through this manager
"""
from typing import Dict, Any, Optional
from src.core.universal_cache import UniversalCache
from src.errors.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)


class MetadataManager:
    """
    Manages all metadata operations for customers/clients and business
    Single point of access for all cache operations
    """
    
    def __init__(self, universal_cache: UniversalCache, business: Optional[str] = None):
        """
        Initialize metadata manager
        
        Args:
            universal_cache: UniversalCache instance
            business: Business identifier (optional)
        """
        self.cache = universal_cache
        self.business = business
        
        # Ensure cache is loaded
        if not self.cache.is_loaded:
            self.cache.load()
        
        # Initialize business field if provided
        if business:
            self._initialize_business_field(business)
    
    def _ensure_loaded(self) -> None:
        """Ensure cache is loaded"""
        if not self.cache.is_loaded:
            self.cache.load()
    
    def _initialize_business_field(self, business: str) -> None:
        """
        Initialize business field in metadata
        
        Args:
            business: Business identifier
        """
        self._ensure_loaded()
        self.cache.acquire_write_lock()
        try:
            # Ensure metadata exists
            if "metadata" not in self.cache.data:
                self.cache.data["metadata"] = {}
            
            # Set business field
            self.cache.data["metadata"]["business"] = business
            
            # Save changes
            self.cache.save()
            logger.info(f"Initialized business field: {business}")
        finally:
            self.cache.release_write_lock()
    
    def _read(self, key: str) -> Optional[Dict[str, Any]]:
        """
        [SYSTEM ONLY] Read value from cache with read lock
        
        Args:
            key: Cache key
        
        Returns:
            Value or None
        """
        self._ensure_loaded()
        self.cache.acquire_read_lock()
        try:
            return self.cache.data.get(key)
        finally:
            self.cache.release_read_lock()
    
    def _read_all(self) -> Dict[str, Any]:
        """
        [SYSTEM ONLY] Read entire cache with read lock
        
        Returns:
            Copy of entire cache
        """
        self._ensure_loaded()
        self.cache.acquire_read_lock()
        try:
            return self.cache.data.copy()
        finally:
            self.cache.release_read_lock()
    
    def _write(self, key: str, value: Dict[str, Any]) -> None:
        """
        [SYSTEM ONLY] Write value to cache with write lock
        
        Args:
            key: Cache key
            value: Value to write
        """
        self._ensure_loaded()
        self.cache.acquire_write_lock()
        try:
            self.cache.data[key] = value
            self.cache.save()
        finally:
            self.cache.release_write_lock()
    
    def _update(self, key: str, updates: Dict[str, Any]) -> None:
        """
        [SYSTEM ONLY] Update existing cache entry with write lock
        
        Args:
            key: Cache key
            updates: Dictionary of updates to merge
        """
        self._ensure_loaded()
        self.cache.acquire_write_lock()
        try:
            if key in self.cache.data:
                self.cache.data[key].update(updates)
            else:
                self.cache.data[key] = updates
            self.cache.save()
        finally:
            self.cache.release_write_lock()
    
    def _delete(self, key: str) -> None:
        """
        [SYSTEM ONLY] Delete from cache with write lock
        
        Args:
            key: Cache key
        """
        self._ensure_loaded()
        self.cache.acquire_write_lock()
        try:
            if key in self.cache.data:
                del self.cache.data[key]
            self.cache.save()
        finally:
            self.cache.release_write_lock()
    
    def _update_metadata(self, phone: str, seq_id: int, session_id: str, 
                        version: int) -> None:
        """
        [SYSTEM ONLY] Update metadata with new session
        
        Args:
            phone: Customer phone number
            seq_id: Sequential ID
            session_id: Session ID
            version: Version number
        """
        metadata = self._read(phone)
        
        if metadata is None:
            metadata = {}
        
        # Add version entry
        metadata[str(version)] = session_id
        
        # Update latest_version
        metadata["latest_version"] = version
        
        # Update cache
        self._update(phone, metadata)

    # ============ USER-CALLABLE FUNCTIONS ============
    def get_business_metadata(self) -> Dict[str, Any]:
        """
        [USER CALLABLE] Get business metadata
        
        Returns:
            Business metadata dictionary
        """
        metadata = self._read_all()
        logger.info("Retrieved business metadata")
        return metadata
    
    def get_phone_mapping(self, phone: str, update_default: Optional[str] = None, load_entity_context: bool = True) -> Optional[str]:
        """
        [USER CALLABLE] Get entity type for phone number
        If not found, update cache according to update_default or return None
        
        Args:
            phone: Phone number
            update_default: Default entity type to add if not found ("customer", "client", or None)
            load_entity_context: Whether to add phone mapping if not found (default: True)
        
        Returns:
            Entity type ("customer" or "client") or None if not found and load_entity_context=False
        
        Raises:
            ValueError: If phone not found and load_entity_context is True but update_default is None/invalid
        """
        metadata = self._read_all()
        phone_mappings = metadata.get("phone_mappings", {})
        entity_type = phone_mappings.get(phone)
        
        #if is a new entity:
        is_new_entity = False

        if entity_type:
            logger.info(f"Phone {phone} mapped to: {entity_type}")
            return entity_type, is_new_entity
        
        # Phone not found
        if not load_entity_context:
            logger.warning(f"Phone {phone} not found in mappings and load_entity_context is False")
            return None, None
        
        # Load entity context - update according to update_default
        if update_default is None:
            raise ValueError(f"Phone {phone} not found in mappings and no default provided")
        
        if update_default not in ["customer", "client"]:
            raise ValueError(f"Invalid update_default: {update_default}. Must be 'customer' or 'client'")
        
        # Add phone mapping and increment count
        self._add_phone_mapping(phone, update_default)
        logger.info(f"Phone {phone} not found, added as {update_default}")
        
        is_new_entity = True

        return update_default, is_new_entity
    
    def add_phone_mapping(self, phone: str, entity_type: str) -> None:
        """
        [USER CALLABLE] Add phone to entity type mapping
        
        Args:
            phone: Phone number
            entity_type: Entity type ("customer" or "client")
        """
        self._add_phone_mapping(phone, entity_type)
    
    # ============ SYSTEM-ONLY FUNCTIONS ============
    def _add_phone_mapping(self, phone: str, entity_type: str) -> None:
        """
        [SYSTEM ONLY] Add phone to entity type mapping and update counts
        
        Args:
            phone: Phone number
            entity_type: Entity type ("customer" or "client")
        """
        if entity_type not in ["customer", "client"]:
            raise ValueError(f"Invalid entity type: {entity_type}")
        
        metadata = self._read_all()
        phone_mappings = metadata.get("phone_mappings", {})
        phone_mappings[phone] = entity_type
        
        self._update("phone_mappings", phone_mappings)
        logger.info(f"Added phone mapping: {phone} → {entity_type}")
        
        # Increment appropriate count
        if entity_type == "customer":
            self._increment_customer_count()
        elif entity_type == "client":
            self._increment_client_count()
    
    def _remove_phone_mapping(self, phone: str) -> None:
        """
        [SYSTEM ONLY] Remove phone from entity type mapping and decrement counts
        
        Args:
            phone: Phone number
        """
        metadata = self._read_all()
        phone_mappings = metadata.get("phone_mappings", {})
        
        if phone not in phone_mappings:
            logger.warning(f"Phone {phone} not found in mappings, nothing to remove")
            return
        
        entity_type = phone_mappings[phone]
        del phone_mappings[phone]
        
        self._update("phone_mappings", phone_mappings)
        logger.info(f"Removed phone mapping: {phone}")
        
        # Decrement appropriate count
        if entity_type == "customer":
            self._decrement_customer_count()
        elif entity_type == "client":
            self._decrement_client_count()
    
    def _decrement_customer_count(self) -> None:
        """[SYSTEM ONLY] Decrement total customers count"""
        metadata = self._read_all()
        business_meta = metadata.get("metadata", {})
        business_meta["total_customers"] = max(0, business_meta.get("total_customers", 1) - 1)
        
        self._update("metadata", business_meta)
        logger.info(f"Decremented customer count to {business_meta['total_customers']}")
    
    def _decrement_client_count(self) -> None:
        """[SYSTEM ONLY] Decrement total clients count"""
        metadata = self._read_all()
        business_meta = metadata.get("metadata", {})
        business_meta["total_clients"] = max(0, business_meta.get("total_clients", 1) - 1)
        
        self._update("metadata", business_meta)
        logger.info(f"Decremented client count to {business_meta['total_clients']}")
    
    def _update_business_metadata(self, updates: Dict[str, Any]) -> None:
        """
        [SYSTEM ONLY] Update business metadata
        
        Args:
            updates: Dictionary of updates to merge
        """
        for key, value in updates.items():
            self._update(key, value)
        logger.info("Updated business metadata")
    
    def _increment_customer_count(self) -> None:
        """[SYSTEM ONLY] Increment total customers count"""
        metadata = self._read_all()
        business_meta = metadata.get("metadata", {})
        business_meta["total_customers"] = business_meta.get("total_customers", 0) + 1
        
        self._update("metadata", business_meta)
        logger.info(f"Incremented customer count to {business_meta['total_customers']}")
    
    def _increment_client_count(self) -> None:
        """[SYSTEM ONLY] Increment total clients count"""
        metadata = self._read_all()
        business_meta = metadata.get("metadata", {})
        business_meta["total_clients"] = business_meta.get("total_clients", 0) + 1
        
        self._update("metadata", business_meta)
        logger.info(f"Incremented client count to {business_meta['total_clients']}")
    
    def _get_total_customers(self) -> int:
        """[SYSTEM ONLY] Get total customers count"""
        metadata = self._read_all()
        business_meta = metadata.get("metadata", {})
        return business_meta.get("total_customers", 0)
    
    def _get_total_clients(self) -> int:
        """[SYSTEM ONLY] Get total clients count"""
        metadata = self._read_all()
        business_meta = metadata.get("metadata", {})
        return business_meta.get("total_clients", 0)
