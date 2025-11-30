"""
Chatbot API routes - FastAPI endpoints for WhatsApp integration
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging
import os

from src.chatbot_layer.core.whatsapp_handler import WhatsAppHandler
from src.chatbot_layer.core.chatbot_engine import ChatbotEngine

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/v1/chatbot", tags=["chatbot"])

# Initialize WhatsApp handler and chatbot engine
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "your_phone_id")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "your_access_token")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "your_verify_token")

whatsapp_handler = WhatsAppHandler(
    phone_number_id=WHATSAPP_PHONE_ID,
    access_token=WHATSAPP_ACCESS_TOKEN,
    verify_token=WHATSAPP_VERIFY_TOKEN
)

chatbot_engine = ChatbotEngine(whatsapp_handler)


@router.get("/webhook")
async def verify_webhook(request: Request) -> Dict[str, Any]:
    """
    Verify WhatsApp webhook
    
    Query params:
        hub.mode: "subscribe"
        hub.challenge: Challenge string
        hub.verify_token: Verification token
    """
    try:
        mode = request.query_params.get("hub.mode")
        challenge = request.query_params.get("hub.challenge")
        verify_token = request.query_params.get("hub.verify_token")
        
        if mode != "subscribe":
            raise HTTPException(status_code=403, detail="Invalid mode")
        
        result = whatsapp_handler.verify_webhook(verify_token, challenge)
        if result:
            return {"challenge": result}
        else:
            raise HTTPException(status_code=403, detail="Invalid verification token")
    
    except Exception as e:
        logger.error(f"Webhook verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/webhook")
async def handle_webhook(request: Request) -> Dict[str, str]:
    """
    Handle incoming WhatsApp messages
    
    Receives webhook data from WhatsApp and processes messages
    """
    try:
        webhook_data = await request.json()
        
        logger.info(f"Received webhook: {webhook_data}")
        
        # Parse incoming message
        message_data = whatsapp_handler.parse_incoming_message(webhook_data)
        
        if message_data:
            # Mark message as read
            whatsapp_handler.mark_message_as_read(message_data.get("message_id"))
            
            # Handle message asynchronously
            await chatbot_engine.handle_incoming_message(message_data)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Webhook handling error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "chatbot-layer",
        "version": "1.0.0"
    }


@router.get("/conversation/{customer_phone}")
async def get_conversation(customer_phone: str) -> Dict[str, Any]:
    """
    Get conversation state for a customer
    
    Args:
        customer_phone: Customer phone number
    
    Returns:
        Conversation data
    """
    try:
        conversation = chatbot_engine.conversation_manager.get_conversation(customer_phone)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "result": {
                "response": conversation,
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/{customer_phone}/reset")
async def reset_conversation(customer_phone: str) -> Dict[str, Any]:
    """
    Reset conversation for a customer
    
    Args:
        customer_phone: Customer phone number
    
    Returns:
        Success response
    """
    try:
        chatbot_engine.conversation_manager.reset_conversation(customer_phone)
        
        return {
            "result": {
                "response": {"message": "Conversation reset"},
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_all_conversations() -> Dict[str, Any]:
    """
    Get all active conversations
    
    Returns:
        List of all conversations
    """
    try:
        conversations = chatbot_engine.conversation_manager.conversations
        
        return {
            "result": {
                "response": {
                    "total_conversations": len(conversations),
                    "conversations": list(conversations.values())
                },
                "status": "SUCCESS"
            },
            "err_details": {}
        }
    
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
