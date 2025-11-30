"""
Chatbot Engine - Main orchestrator for chatbot logic
Handles conversation flow and integrates with backend APIs
"""
import logging
import json
from typing import Dict, Any, Optional
import httpx

from src.chatbot_layer.core.conversation_state import ConversationManager, ConversationState
from src.chatbot_layer.core.whatsapp_handler import WhatsAppHandler

logger = logging.getLogger(__name__)


class ChatbotEngine:
    """Main chatbot engine"""
    
    def __init__(self, whatsapp_handler: WhatsAppHandler, backend_url: str = "http://localhost:8000"):
        """
        Initialize chatbot engine
        
        Args:
            whatsapp_handler: WhatsApp handler instance
            backend_url: Backend API URL
        """
        self.whatsapp = whatsapp_handler
        self.conversation_manager = ConversationManager()
        self.backend_url = backend_url
    
    async def handle_incoming_message(self, message_data: Dict[str, Any]) -> None:
        """
        Handle incoming message from customer
        
        Args:
            message_data: Parsed message data from WhatsApp
        """
        try:
            customer_phone = message_data.get("customer_phone")
            message_content = message_data.get("content", "").strip().lower()
            
            logger.info(f"Handling message from {customer_phone}: {message_content}")
            
            # Get or create conversation
            conversation = self.conversation_manager.get_or_create_conversation(customer_phone)
            current_state = self.conversation_manager.get_state(customer_phone)
            
            # Increment message count
            self.conversation_manager.increment_message_count(customer_phone)
            
            # Route to appropriate handler based on state
            if current_state == ConversationState.GREETING:
                await self._handle_greeting(customer_phone, message_content)
            
            elif current_state == ConversationState.COLLECTING_NAME:
                await self._handle_name_input(customer_phone, message_content)
            
            elif current_state == ConversationState.COLLECTING_LOCATION:
                await self._handle_location_input(customer_phone, message_data)
            
            elif current_state == ConversationState.SEARCHING_SALONS:
                await self._handle_salon_search(customer_phone, message_content)
            
            elif current_state == ConversationState.VIEWING_SALON:
                await self._handle_salon_selection(customer_phone, message_content)
            
            elif current_state == ConversationState.SELECTING_SERVICE:
                await self._handle_service_selection(customer_phone, message_content)
            
            elif current_state == ConversationState.SELECTING_SLOT:
                await self._handle_slot_selection(customer_phone, message_content)
            
            elif current_state == ConversationState.CONFIRMING_BOOKING:
                await self._handle_booking_confirmation(customer_phone, message_content)
            
            else:
                await self._handle_default(customer_phone)
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            await self._send_error_message(customer_phone)
    
    async def _handle_greeting(self, customer_phone: str, message_content: str) -> None:
        """Handle greeting state"""
        response = "Hi! Welcome to Salon Booking 👋\n\nWhat's your name?"
        self.whatsapp.send_text_message(customer_phone, response)
        self.conversation_manager.update_state(customer_phone, ConversationState.COLLECTING_NAME)
    
    async def _handle_name_input(self, customer_phone: str, message_content: str) -> None:
        """Handle name input"""
        if len(message_content) < 2:
            response = "Please enter a valid name (at least 2 characters)"
            self.whatsapp.send_text_message(customer_phone, response)
            return
        
        self.conversation_manager.update_data(customer_phone, "name", message_content)
        
        response = f"Nice to meet you, {message_content.title()}! 😊\n\nPlease share your location so we can find nearby salons."
        self.whatsapp.send_text_message(customer_phone, response)
        self.conversation_manager.update_state(customer_phone, ConversationState.COLLECTING_LOCATION)
    
    async def _handle_location_input(self, customer_phone: str, message_data: Dict[str, Any]) -> None:
        """Handle location input"""
        # Extract location from message
        raw_data = message_data.get("raw_data", {})
        location = raw_data.get("location")
        
        if location:
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            self.conversation_manager.update_data(customer_phone, "location", {
                "latitude": latitude,
                "longitude": longitude
            })
            
            response = "Great! Location saved. 📍\n\nWhat service are you looking for?\n\n1. Hair Cutting\n2. Hair Coloring\n3. Facial Treatment\n4. Manicure\n5. Pedicure\n6. Massage Therapy"
            self.whatsapp.send_text_message(customer_phone, response)
            self.conversation_manager.update_state(customer_phone, ConversationState.SELECTING_SERVICE)
        else:
            response = "Please share your location to find nearby salons."
            self.whatsapp.send_text_message(customer_phone, response)
    
    async def _handle_service_selection(self, customer_phone: str, message_content: str) -> None:
        """Handle service selection"""
        services = {
            "1": "hair-cutting",
            "2": "hair-coloring",
            "3": "facial-treatment",
            "4": "manicure",
            "5": "pedicure",
            "6": "massage-therapy"
        }
        
        service_type = services.get(message_content)
        if not service_type:
            response = "Please select a valid option (1-6)"
            self.whatsapp.send_text_message(customer_phone, response)
            return
        
        self.conversation_manager.update_data(customer_phone, "service_type", service_type)
        
        # Search for salons
        await self._search_salons(customer_phone, service_type)
    
    async def _search_salons(self, customer_phone: str, service_type: str) -> None:
        """Search for salons via backend API"""
        try:
            location = self.conversation_manager.get_data(customer_phone, "location")
            
            # Call backend API to get salon suggestions
            payload = {
                "phone": customer_phone,
                "business": "salon",
                "action": "get-customer_booking_map",
                "service_name": service_type,
                "location": location,
                "request_time": "2025-11-23T18:50:00Z"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.backend_url}/api/v1/getcustomerbookingmapping/{service_type}/{service_type}/{customer_phone}",
                    json=payload,
                    timeout=10
                )
            
            if response.status_code == 200:
                result = response.json()
                salons = result.get("result", {}).get("response", {}).get("salons", [])
                
                if salons:
                    # Format salon list
                    salon_list = "\n".join([
                        f"{i+1}. {salon.get('salonName')} - {salon.get('distance')}km away"
                        for i, salon in enumerate(salons[:5])
                    ])
                    
                    response_text = f"Found {len(salons)} salons! Here are the top 5:\n\n{salon_list}\n\nReply with the number to select a salon."
                    self.whatsapp.send_text_message(customer_phone, response_text)
                    self.conversation_manager.update_state(customer_phone, ConversationState.VIEWING_SALON)
                else:
                    response_text = "Sorry, no salons found for this service in your area. Try another service."
                    self.whatsapp.send_text_message(customer_phone, response_text)
            else:
                await self._send_error_message(customer_phone)
        
        except Exception as e:
            logger.error(f"Error searching salons: {str(e)}")
            await self._send_error_message(customer_phone)
    
    async def _handle_salon_selection(self, customer_phone: str, message_content: str) -> None:
        """Handle salon selection"""
        try:
            salon_index = int(message_content) - 1
            if salon_index < 0 or salon_index > 4:
                response = "Please select a valid salon (1-5)"
                self.whatsapp.send_text_message(customer_phone, response)
                return
            
            # Store selected salon
            self.conversation_manager.update_data(customer_phone, "selected_salon_index", salon_index)
            
            response = "Perfect! Now let's check available time slots.\n\nAvailable slots:\n\n1. 10:00 AM\n2. 11:00 AM\n3. 2:00 PM\n4. 3:00 PM\n5. 4:00 PM\n\nReply with the number to select a slot."
            self.whatsapp.send_text_message(customer_phone, response)
            self.conversation_manager.update_state(customer_phone, ConversationState.SELECTING_SLOT)
        
        except ValueError:
            response = "Please reply with a number (1-5)"
            self.whatsapp.send_text_message(customer_phone, response)
    
    async def _handle_slot_selection(self, customer_phone: str, message_content: str) -> None:
        """Handle time slot selection"""
        try:
            slot_index = int(message_content) - 1
            if slot_index < 0 or slot_index > 4:
                response = "Please select a valid slot (1-5)"
                self.whatsapp.send_text_message(customer_phone, response)
                return
            
            slots = ["10:00 AM", "11:00 AM", "2:00 PM", "3:00 PM", "4:00 PM"]
            selected_slot = slots[slot_index]
            self.conversation_manager.update_data(customer_phone, "selected_slot", selected_slot)
            
            # Show booking confirmation
            name = self.conversation_manager.get_data(customer_phone, "name")
            service = self.conversation_manager.get_data(customer_phone, "service_type")
            
            response = f"Booking Summary:\n\n👤 Name: {name}\n🏢 Salon: Beauty Bliss\n💇 Service: {service.replace('-', ' ').title()}\n⏰ Time: {selected_slot}\n💰 Price: $25\n\nConfirm booking? (Yes/No)"
            self.whatsapp.send_text_message(customer_phone, response)
            self.conversation_manager.update_state(customer_phone, ConversationState.CONFIRMING_BOOKING)
        
        except ValueError:
            response = "Please reply with a number (1-5)"
            self.whatsapp.send_text_message(customer_phone, response)
    
    async def _handle_booking_confirmation(self, customer_phone: str, message_content: str) -> None:
        """Handle booking confirmation"""
        if message_content in ["yes", "y"]:
            # Create booking via backend API
            await self._create_booking(customer_phone)
        elif message_content in ["no", "n"]:
            response = "Booking cancelled. Would you like to search for another salon? (Yes/No)"
            self.whatsapp.send_text_message(customer_phone, response)
            self.conversation_manager.reset_conversation(customer_phone)
        else:
            response = "Please reply with Yes or No"
            self.whatsapp.send_text_message(customer_phone, response)
    
    async def _create_booking(self, customer_phone: str) -> None:
        """Create booking via backend API"""
        try:
            name = self.conversation_manager.get_data(customer_phone, "name")
            service_type = self.conversation_manager.get_data(customer_phone, "service_type")
            
            payload = {
                "phone": customer_phone,
                "name": name,
                "business": "salon",
                "service_type": service_type,
                "action": "CREATE-BOOKING"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.backend_url}/api/v1/makerequest",
                    json=payload,
                    timeout=10
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result", {}).get("status") == "SUCCESS":
                    response_text = "✅ Booking confirmed!\n\nYour appointment has been booked. You'll receive a confirmation shortly.\n\nThank you for using Salon Booking!"
                    self.whatsapp.send_text_message(customer_phone, response_text)
                    self.conversation_manager.update_state(customer_phone, ConversationState.BOOKING_COMPLETE)
                else:
                    await self._send_error_message(customer_phone)
            else:
                await self._send_error_message(customer_phone)
        
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            await self._send_error_message(customer_phone)
    
    async def _handle_salon_search(self, customer_phone: str, message_content: str) -> None:
        """Handle salon search"""
        pass
    
    async def _handle_default(self, customer_phone: str) -> None:
        """Handle default/unknown state"""
        response = "I didn't understand that. Let me start over.\n\nWhat's your name?"
        self.whatsapp.send_text_message(customer_phone, response)
        self.conversation_manager.reset_conversation(customer_phone)
    
    async def _send_error_message(self, customer_phone: str) -> None:
        """Send error message"""
        response = "Sorry, something went wrong. Please try again later."
        self.whatsapp.send_text_message(customer_phone, response)
        self.conversation_manager.update_state(customer_phone, ConversationState.ERROR)
