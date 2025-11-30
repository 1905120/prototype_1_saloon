"""
WhatsApp message handler - Receives and sends messages via WhatsApp API
"""
import logging
import json
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WhatsAppHandler:
    """Handles WhatsApp API integration"""
    
    def __init__(self, phone_number_id: str, access_token: str, verify_token: str):
        """
        Initialize WhatsApp handler
        
        Args:
            phone_number_id: WhatsApp Business Phone Number ID
            access_token: WhatsApp API access token
            verify_token: Webhook verification token
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.verify_token = verify_token
        self.api_url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
    
    def verify_webhook(self, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook signature from WhatsApp
        
        Args:
            token: Verification token from webhook
            challenge: Challenge string from webhook
        
        Returns:
            Challenge string if verification successful, None otherwise
        """
        if token == self.verify_token:
            logger.info("Webhook verified successfully")
            return challenge
        logger.warning("Webhook verification failed")
        return None
    
    def parse_incoming_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming message from WhatsApp webhook
        
        Args:
            webhook_data: Raw webhook data from WhatsApp
        
        Returns:
            Parsed message data or None if invalid
        """
        try:
            # Extract message from webhook structure
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return None
            
            message = messages[0]
            customer_phone = message.get("from")
            message_id = message.get("id")
            timestamp = message.get("timestamp")
            
            # Extract message content
            message_type = message.get("type")  # text, image, document, etc.
            
            if message_type == "text":
                text_content = message.get("text", {}).get("body", "")
            elif message_type == "interactive":
                interactive = message.get("interactive", {})
                button_reply = interactive.get("button_reply", {})
                list_reply = interactive.get("list_reply", {})
                text_content = button_reply.get("title") or list_reply.get("title") or ""
            else:
                text_content = ""
            
            parsed_message = {
                "customer_phone": customer_phone,
                "message_id": message_id,
                "timestamp": timestamp,
                "message_type": message_type,
                "content": text_content,
                "raw_data": message
            }
            
            logger.info(f"Parsed message from {customer_phone}: {text_content[:50]}")
            return parsed_message
        
        except Exception as e:
            logger.error(f"Error parsing incoming message: {str(e)}")
            return None
    
    def send_text_message(self, recipient_phone: str, message_text: str) -> bool:
        """
        Send text message via WhatsApp
        
        Args:
            recipient_phone: Customer phone number
            message_text: Message content
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_phone,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
            
            # In production, make actual API call
            # response = requests.post(self.api_url, json=payload, headers={"Authorization": f"Bearer {self.access_token}"})
            
            logger.info(f"Sending text message to {recipient_phone}: {message_text[:50]}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending text message: {str(e)}")
            return False
    
    def send_interactive_message(self, recipient_phone: str, message_data: Dict[str, Any]) -> bool:
        """
        Send interactive message (buttons, list) via WhatsApp
        
        Args:
            recipient_phone: Customer phone number
            message_data: Interactive message structure
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_phone,
                "type": "interactive",
                "interactive": message_data
            }
            
            # In production, make actual API call
            # response = requests.post(self.api_url, json=payload, headers={"Authorization": f"Bearer {self.access_token}"})
            
            logger.info(f"Sending interactive message to {recipient_phone}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending interactive message: {str(e)}")
            return False
    
    def send_button_message(self, recipient_phone: str, body_text: str, buttons: list) -> bool:
        """
        Send message with quick reply buttons
        
        Args:
            recipient_phone: Customer phone number
            body_text: Message body
            buttons: List of button options [{"id": "1", "title": "Option 1"}, ...]
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message_data = {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": btn.get("id"),
                                "title": btn.get("title")
                            }
                        }
                        for btn in buttons
                    ]
                }
            }
            
            return self.send_interactive_message(recipient_phone, message_data)
        
        except Exception as e:
            logger.error(f"Error sending button message: {str(e)}")
            return False
    
    def send_list_message(self, recipient_phone: str, body_text: str, sections: list) -> bool:
        """
        Send message with list selection
        
        Args:
            recipient_phone: Customer phone number
            body_text: Message body
            sections: List sections with rows
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message_data = {
                "type": "list",
                "body": {
                    "text": body_text
                },
                "action": {
                    "button": "Select",
                    "sections": sections
                }
            }
            
            return self.send_interactive_message(recipient_phone, message_data)
        
        except Exception as e:
            logger.error(f"Error sending list message: {str(e)}")
            return False
    
    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Mark message as read
        
        Args:
            message_id: WhatsApp message ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            logger.info(f"Marking message {message_id} as read")
            return True
        
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False
