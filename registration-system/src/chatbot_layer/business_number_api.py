"""
Business Number API - Endpoints for managing WhatsApp business numbers
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from src.chatbot_layer.core.business_number import BusinessNumberManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/v1/chatbot/business-numbers", tags=["business-numbers"])

# Initialize business number manager
business_number_manager = BusinessNumberManager()


@router.get("/")
async def get_all_business_numbers() -> Dict[str, Any]:
    """
    Get all business numbers
    
    Returns:
        List of all business numbers
    """
    try:
        numbers = business_number_manager.get_all_business_numbers()
        
        return {
            "result": {
                "response": {
                    "total_numbers": len(numbers),
                    "business_numbers": numbers
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except Exception as e:
        logger.error(f"Error getting business numbers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_business_numbers() -> Dict[str, Any]:
    """
    Get all active business numbers
    
    Returns:
        List of active business numbers
    """
    try:
        numbers = business_number_manager.get_active_numbers()
        
        return {
            "result": {
                "response": {
                    "total_active": len(numbers),
                    "business_numbers": numbers
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except Exception as e:
        logger.error(f"Error getting active business numbers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{number_id}")
async def get_business_number(number_id: str) -> Dict[str, Any]:
    """
    Get specific business number
    
    Args:
        number_id: Business number identifier
    
    Returns:
        Business number data
    """
    try:
        number = business_number_manager.get_business_number(number_id)
        
        if not number:
            raise HTTPException(status_code=404, detail="Business number not found")
        
        return {
            "result": {
                "response": number,
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting business number: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_business_number(number_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create new business number
    
    Request body:
    {
        "number_id": "salon_main",
        "phone_id": "your_phone_id",
        "phone_number": "+1-555-0100",
        "display_name": "Salon Booking",
        "business_name": "Salon Booking System",
        "description": "Book salon appointments",
        "features": ["booking", "search"],
        "supported_languages": ["en"],
        "timezone": "UTC"
    }
    
    Returns:
        Created business number data
    """
    try:
        number_id = number_data.get("number_id")
        
        if not number_id:
            raise HTTPException(status_code=400, detail="number_id is required")
        
        # Remove number_id from data before passing to manager
        phone_data = {k: v for k, v in number_data.items() if k != "number_id"}
        
        success = business_number_manager.add_business_number(number_id, phone_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create business number")
        
        created_number = business_number_manager.get_business_number(number_id)
        
        return {
            "result": {
                "response": {
                    "number_id": number_id,
                    "data": created_number,
                    "message": "Business number created successfully"
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating business number: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{number_id}")
async def update_business_number(number_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update business number
    
    Args:
        number_id: Business number identifier
        updates: Fields to update
    
    Returns:
        Updated business number data
    """
    try:
        success = business_number_manager.update_business_number(number_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Business number not found")
        
        updated_number = business_number_manager.get_business_number(number_id)
        
        return {
            "result": {
                "response": {
                    "number_id": number_id,
                    "data": updated_number,
                    "message": "Business number updated successfully"
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating business number: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{number_id}")
async def delete_business_number(number_id: str) -> Dict[str, Any]:
    """
    Delete business number
    
    Args:
        number_id: Business number identifier
    
    Returns:
        Success response
    """
    try:
        success = business_number_manager.delete_business_number(number_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Business number not found")
        
        return {
            "result": {
                "response": {
                    "number_id": number_id,
                    "message": "Business number deleted successfully"
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting business number: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{number_id}/status")
async def update_business_number_status(number_id: str, status_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Update business number status
    
    Args:
        number_id: Business number identifier
        status_data: {"status": "active|inactive|suspended"}
    
    Returns:
        Updated business number data
    """
    try:
        status = status_data.get("status")
        
        if not status:
            raise HTTPException(status_code=400, detail="status is required")
        
        success = business_number_manager.set_number_status(number_id, status)
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid status or business number not found")
        
        updated_number = business_number_manager.get_business_number(number_id)
        
        return {
            "result": {
                "response": {
                    "number_id": number_id,
                    "status": status,
                    "data": updated_number
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{number_id}/features/{feature}")
async def add_feature(number_id: str, feature: str) -> Dict[str, Any]:
    """
    Add feature to business number
    
    Args:
        number_id: Business number identifier
        feature: Feature name (e.g., "booking", "search", "notifications")
    
    Returns:
        Updated business number data
    """
    try:
        success = business_number_manager.add_feature(number_id, feature)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add feature")
        
        updated_number = business_number_manager.get_business_number(number_id)
        
        return {
            "result": {
                "response": {
                    "number_id": number_id,
                    "feature": feature,
                    "data": updated_number
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding feature: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{number_id}/features/{feature}")
async def remove_feature(number_id: str, feature: str) -> Dict[str, Any]:
    """
    Remove feature from business number
    
    Args:
        number_id: Business number identifier
        feature: Feature name to remove
    
    Returns:
        Updated business number data
    """
    try:
        success = business_number_manager.remove_feature(number_id, feature)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove feature")
        
        updated_number = business_number_manager.get_business_number(number_id)
        
        return {
            "result": {
                "response": {
                    "number_id": number_id,
                    "feature": feature,
                    "data": updated_number
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing feature: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
