"""
Client management manager
"""
from typing import Dict, Any, Optional
from src.core.client_management import shared
import logging
import os

logger = logging.getLogger(__name__)


class ClientManager:
    """Manager for client operations with singleton cache"""
    
    def __init__(self):
        """Initialize manager"""
        self._cache = None
        self._business = None
    
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
        if not self._cache:
            raise ValueError("Cache not initialized. Call load_client_metadata first.")
        return self._cache.read_all()
    
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
        return f"data/businesses/{business}/client_metadata.json"
