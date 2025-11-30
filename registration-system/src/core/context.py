"""
Business context - manages business-level components
"""
from typing import Dict, Any
from src.core.universal_cache import UniversalCache
from src.core.metadata_manager import MetadataManager
import logging

logger = logging.getLogger(__name__)


class BusinessContext:
    """
    Business context managing business-level components
    Handles business metadata and operations
    """
    
    def __init__(self, business:str,  business_metadata_path: str, business_meta_schema: str):
        """
        Initialize business context
        
        Args:
            business_metadata_path: Path to business metadata.json file (required)
        
        Raises:
            ValueError: If business_metadata_path is not provided
        """
        if not business_metadata_path:
            raise ValueError("business_metadata_path is required")
        
        # Core infrastructure
        from src.core.universal_cache import get_universal_cache
        
        self.business_cache = get_universal_cache(business_metadata_path, business_meta_schema)
        self.metadata_manager = MetadataManager(self.business_cache, business=business)
        self.phone = None  # Track phone for cleanup
        logger.info(f"BusinessContext initialized with business metadata: {business_metadata_path}")
    
    def destroy(self, phone: str) -> None:
        """
        Destroy business context and cleanup resources
        Removes phone mapping only if it was added during this context
        
        Args:
            phone: Phone number to cleanup
        """
        try:
            # Check if phone mapping was added (using get_phone_mapping with load_entity_context=False)
            entity_type = self.metadata_manager.get_phone_mapping(
                phone, 
                load_entity_context=False
            )
            
            # Only remove if phone mapping exists (entity_type is not None)
            if entity_type is not None:
                self.metadata_manager._remove_phone_mapping(phone)
                logger.info(f"BusinessContext destroyed - cleaned up phone mapping for {phone}")
            else:
                logger.info(f"BusinessContext destroyed - phone {phone} not in mapping, no cleanup needed")
        except Exception as e:
            logger.error(f"Error destroying BusinessContext: {str(e)}")
            raise


class CustomerContext:
    """
    Customer context managing customer-level components
    Handles customer metadata and operations
    """
    
    def __init__(self, business: str):
        """
        Initialize customer context
        
        Args:
            business: Business identifier (required)
        
        Raises:
            ValueError: If business is not provided
        """
        if not business:
            raise ValueError("business is required")
        
        # Core infrastructure - manager handles shared cache internally
        from src.core.customer_management.manager import CustomerManager
        
        # Initialize manager
        self.customer_manager = CustomerManager(business)
        
        # Load customer metadata for business (singleton cache)
        self.customer_manager.load_customer_metadata()
        self._business = business
        self._action = None
        logger.info(f"CustomerContext initialized for business: {business}")
    
    def destroy(self) -> None:
        """Destroy customer context and cleanup cache"""
        try:
            self.customer_manager.destroy_cache(self._business)
            logger.info(f"CustomerContext destroyed for business: {self._business}")
        except Exception as e:
            logger.error(f"Error destroying CustomerContext: {str(e)}")
            raise


class ClientContext:
    """
    Client context managing client-level components
    Handles client metadata and operations
    """
    
    def __init__(self, business: str):
        """
        Initialize client context
        
        Args:
            business: Business identifier (required)
        
        Raises:
            ValueError: If business is not provided
        """
        if not business:
            raise ValueError("business is required")
        
        # Core infrastructure - manager handles shared cache internally
        from src.core.client_management.manager import ClientManager
        
        # Initialize manager
        self.client_manager = ClientManager(business)
        
        # Load client metadata for business (singleton cache)
        self.client_manager.load_client_metadata(business)
        self._business = business
        self._action = None
        logger.info(f"ClientContext initialized for business: {business}")
    
    def destroy(self) -> None:
        """Destroy client context and cleanup cache"""
        try:
            self.client_manager.destroy_cache(self._business)
            logger.info(f"ClientContext destroyed for business: {self._business}")
        except Exception as e:
            logger.error(f"Error destroying ClientContext: {str(e)}")
            raise

