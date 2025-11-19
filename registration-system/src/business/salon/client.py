"""
Client business logic for salon operations
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class Client:
    """Client business logic handler"""
    
    async def create(self, payload: Dict[str, Any], cache_data: Dict[str, Any], entity_id: str, seq_id: int) -> Dict[str, Any]:
        """Create new client"""
        try:
            logger.info(f"Creating client with entity_id: {entity_id}, seq_id: {seq_id}")
            
            client_key = payload.phone
            cache_data[client_key] = {
                "id": entity_id,
                "phone": payload.phone,
                "owner_name": payload.owner_name,
                "salon_name": payload.salon_name,
                "service_type": payload.service_type,
                "business": payload.business,
                "working_hours": payload.working_hours or [],
                "created_at": __import__('datetime').datetime.now().isoformat(),
                "seq_id": seq_id
            }
            
            return {
                "status": "SUCCESS",
                "entity_id": entity_id,
                "seq_id": seq_id,
                "message": "Client created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating client: {str(e)}")
            return {
                "status": "FAILED",
                "error": str(e),
                "message": "Failed to create client"
            }
    
    async def update(self, payload: Dict[str, Any], cache_data: Dict[str, Any], entity_id: str, seq_id: int) -> Dict[str, Any]:
        """Update existing client"""
        try:
            logger.info(f"Updating client with entity_id: {entity_id}, seq_id: {seq_id}")
            
            client_key = payload.phone
            if client_key not in cache_data:
                return {
                    "status": "FAILED",
                    "error": f"Client not found: {client_key}",
                    "message": "Client does not exist"
                }
            
            client = cache_data[client_key]
            client.update(payload.updates or {})
            client["updated_at"] = __import__('datetime').datetime.now().isoformat()
            client["seq_id"] = seq_id
            
            return {
                "status": "SUCCESS",
                "entity_id": entity_id,
                "seq_id": seq_id,
                "message": "Client updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating client: {str(e)}")
            return {
                "status": "FAILED",
                "error": str(e),
                "message": "Failed to update client"
            }
    
    async def delete(self, payload: Dict[str, Any], cache_data: Dict[str, Any], entity_id: str, seq_id: int) -> Dict[str, Any]:
        """Delete client (soft delete)"""
        try:
            logger.info(f"Deleting client with entity_id: {entity_id}, seq_id: {seq_id}")
            
            client_key = payload.phone
            if client_key not in cache_data:
                return {
                    "status": "FAILED",
                    "error": f"Client not found: {client_key}",
                    "message": "Client does not exist"
                }
            
            client = cache_data[client_key]
            client["deleted"] = True
            client["deleted_at"] = __import__('datetime').datetime.now().isoformat()
            client["seq_id"] = seq_id
            
            return {
                "status": "SUCCESS",
                "entity_id": entity_id,
                "seq_id": seq_id,
                "message": "Client deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting client: {str(e)}")
            return {
                "status": "FAILED",
                "error": str(e),
                "message": "Failed to delete client"
            }
