"""
Conversation state manager - Tracks conversation state per customer
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation states"""
    IDLE = "idle"
    GREETING = "greeting"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_LOCATION = "collecting_location"
    SEARCHING_SALONS = "searching_salons"
    VIEWING_SALON = "viewing_salon"
    SELECTING_SERVICE = "selecting_service"
    SELECTING_SLOT = "selecting_slot"
    CONFIRMING_BOOKING = "confirming_booking"
    BOOKING_COMPLETE = "booking_complete"
    ERROR = "error"


class ConversationManager:
    """Manages conversation state for each customer"""
    
    def __init__(self):
        """Initialize conversation manager"""
        self.conversations: Dict[str, Dict[str, Any]] = {}
    
    def get_or_create_conversation(self, customer_phone: str) -> Dict[str, Any]:
        """
        Get existing conversation or create new one
        
        Args:
            customer_phone: Customer phone number
        
        Returns:
            Conversation data dictionary
        """
        if customer_phone not in self.conversations:
            self.conversations[customer_phone] = {
                "customer_phone": customer_phone,
                "state": ConversationState.GREETING.value,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "data": {
                    "name": None,
                    "location": None,
                    "service_type": None,
                    "selected_salon": None,
                    "selected_slot": None,
                    "booking_details": None
                },
                "message_count": 0
            }
            logger.info(f"Created new conversation for {customer_phone}")
        
        return self.conversations[customer_phone]
    
    def update_state(self, customer_phone: str, new_state: ConversationState) -> None:
        """
        Update conversation state
        
        Args:
            customer_phone: Customer phone number
            new_state: New conversation state
        """
        conversation = self.get_or_create_conversation(customer_phone)
        conversation["state"] = new_state.value
        conversation["last_updated"] = datetime.now().isoformat()
        logger.info(f"Updated state for {customer_phone} to {new_state.value}")
    
    def update_data(self, customer_phone: str, key: str, value: Any) -> None:
        """
        Update conversation data
        
        Args:
            customer_phone: Customer phone number
            key: Data key
            value: Data value
        """
        conversation = self.get_or_create_conversation(customer_phone)
        conversation["data"][key] = value
        conversation["last_updated"] = datetime.now().isoformat()
        logger.info(f"Updated data for {customer_phone}: {key} = {value}")
    
    def get_data(self, customer_phone: str, key: str) -> Optional[Any]:
        """
        Get conversation data
        
        Args:
            customer_phone: Customer phone number
            key: Data key
        
        Returns:
            Data value or None
        """
        conversation = self.get_or_create_conversation(customer_phone)
        return conversation["data"].get(key)
    
    def get_state(self, customer_phone: str) -> ConversationState:
        """
        Get current conversation state
        
        Args:
            customer_phone: Customer phone number
        
        Returns:
            Current conversation state
        """
        conversation = self.get_or_create_conversation(customer_phone)
        state_value = conversation["state"]
        return ConversationState(state_value)
    
    def increment_message_count(self, customer_phone: str) -> int:
        """
        Increment message count
        
        Args:
            customer_phone: Customer phone number
        
        Returns:
            Updated message count
        """
        conversation = self.get_or_create_conversation(customer_phone)
        conversation["message_count"] += 1
        return conversation["message_count"]
    
    def reset_conversation(self, customer_phone: str) -> None:
        """
        Reset conversation to initial state
        
        Args:
            customer_phone: Customer phone number
        """
        if customer_phone in self.conversations:
            del self.conversations[customer_phone]
            logger.info(f"Reset conversation for {customer_phone}")
    
    def get_conversation(self, customer_phone: str) -> Optional[Dict[str, Any]]:
        """
        Get full conversation data
        
        Args:
            customer_phone: Customer phone number
        
        Returns:
            Conversation data or None
        """
        return self.conversations.get(customer_phone)
    
    def clear_all(self) -> None:
        """Clear all conversations"""
        self.conversations.clear()
        logger.info("Cleared all conversations")
