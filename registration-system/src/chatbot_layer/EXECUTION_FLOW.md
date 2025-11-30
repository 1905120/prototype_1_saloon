# Chatbot Layer - Execution Flow

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     WhatsApp Customer                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Message
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  WhatsApp Business API                           │
│              (Meta/Facebook Infrastructure)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Webhook POST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Server                                │
│                   (main.py running)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              POST /v1/chatbot/webhook                            │
│           (Chatbot API Route Handler)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           WhatsAppHandler.parse_incoming_message()              │
│         (Extract phone, message, type from webhook)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│        ChatbotEngine.handle_incoming_message()                  │
│      (Route to appropriate handler based on state)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│      ConversationManager.get_or_create_conversation()           │
│         (Get/create conversation state for customer)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         State-specific Handler (e.g., _handle_greeting)         │
│    (Process message based on current conversation state)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│      WhatsAppHandler.send_text_message()                        │
│         (Send response back to customer)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  WhatsApp Business API                           │
│              (Send message to customer)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     WhatsApp Customer                            │
│                  (Receives message)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Step-by-Step Execution Flow

### Phase 1: System Initialization

```
1. Server Startup (main.py)
   ├─ FastAPI app initialized
   ├─ Lifespan context manager starts
   ├─ Worker pool initialized
   ├─ Queue manager initialized
   └─ All routers included:
      ├─ salon_router
      ├─ payments_router
      ├─ chatbot_router
      └─ business_number_router

2. Chatbot Layer Initialization (api.py)
   ├─ WhatsAppHandler created
   │  ├─ phone_number_id = from env
   │  ├─ access_token = from env
   │  └─ verify_token = from env
   ├─ ChatbotEngine created
   │  ├─ whatsapp_handler assigned
   │  ├─ ConversationManager initialized (empty)
   │  └─ backend_url = "http://localhost:8000"
   └─ BusinessNumberManager created
      ├─ Loads config from data/chatbot/business_numbers.json
      └─ Creates default config if not exists

3. Business Number Initialization (business_number.py)
   ├─ Check if config file exists
   ├─ If not, create default:
   │  └─ salon_main: +1-555-0100 (active)
   └─ Load all business numbers into memory
```

### Phase 2: Webhook Verification (First Time Setup)

```
Customer/Admin Action:
  └─ Configure WhatsApp webhook in Meta Dashboard
     └─ Points to: https://your-domain/v1/chatbot/webhook

WhatsApp sends verification request:
  └─ GET /v1/chatbot/webhook?hub.mode=subscribe&hub.challenge=XXX&hub.verify_token=YYY

Server Processing:
  1. handle_webhook() receives GET request
  2. Extract query parameters:
     ├─ mode = "subscribe"
     ├─ challenge = "XXX"
     └─ verify_token = "YYY"
  3. Call whatsapp_handler.verify_webhook(verify_token, challenge)
  4. Compare verify_token with stored WHATSAPP_VERIFY_TOKEN
  5. If match:
     └─ Return {"challenge": challenge}
  6. If no match:
     └─ Return 403 Forbidden

WhatsApp:
  └─ Receives challenge response
  └─ Webhook verified ✓
```

### Phase 3: Customer Sends First Message

```
Customer Action:
  └─ Opens WhatsApp
  └─ Finds business number (+1-555-0100)
  └─ Sends message: "Hi"

WhatsApp Infrastructure:
  └─ Receives message
  └─ Sends webhook POST to: https://your-domain/v1/chatbot/webhook
  └─ Payload:
     {
       "entry": [{
         "changes": [{
           "value": {
             "messages": [{
               "from": "1234567890",
               "id": "msg_id_123",
               "timestamp": "1700000000",
               "type": "text",
               "text": {"body": "Hi"}
             }]
           }
         }]
       }]
     }

Server Processing:
  1. POST /v1/chatbot/webhook receives webhook
  2. Parse JSON body
  3. Call whatsapp_handler.parse_incoming_message(webhook_data)
     ├─ Extract from nested structure
     ├─ Get customer_phone = "1234567890"
     ├─ Get message_id = "msg_id_123"
     ├─ Get message_type = "text"
     ├─ Get content = "Hi"
     └─ Return parsed_message dict
  4. Call whatsapp_handler.mark_message_as_read(message_id)
  5. Call await chatbot_engine.handle_incoming_message(message_data)
```

### Phase 4: Chatbot Engine Processing

```
ChatbotEngine.handle_incoming_message(message_data):
  1. Extract customer_phone = "1234567890"
  2. Extract message_content = "hi"
  3. Log: "Handling message from 1234567890: hi"
  
  4. Get or create conversation:
     └─ conversation_manager.get_or_create_conversation("1234567890")
        ├─ Check if "1234567890" in conversations dict
        ├─ If not, create new:
        │  {
        │    "customer_phone": "1234567890",
        │    "state": "greeting",
        │    "created_at": "2025-11-23T18:50:00Z",
        │    "data": {
        │      "name": null,
        │      "location": null,
        │      "service_type": null,
        │      "selected_salon": null,
        │      "selected_slot": null,
        │      "booking_details": null
        │    },
        │    "message_count": 0
        │  }
        └─ Return conversation dict
  
  5. Get current state:
     └─ current_state = conversation_manager.get_state("1234567890")
        └─ Returns: ConversationState.GREETING
  
  6. Increment message count:
     └─ conversation_manager.increment_message_count("1234567890")
        └─ message_count = 1
  
  7. Route based on state:
     └─ if current_state == ConversationState.GREETING:
        └─ await _handle_greeting("1234567890", "hi")
```

### Phase 5: State Handler - Greeting

```
_handle_greeting(customer_phone, message_content):
  1. Create response:
     └─ response = "Hi! Welcome to Salon Booking 👋\n\nWhat's your name?"
  
  2. Send message:
     └─ whatsapp_handler.send_text_message("1234567890", response)
        ├─ Create payload:
        │  {
        │    "messaging_product": "whatsapp",
        │    "to": "1234567890",
        │    "type": "text",
        │    "text": {"body": response}
        │  }
        ├─ Log: "Sending text message to 1234567890: Hi! Welcome..."
        └─ Return True (in production, would call WhatsApp API)
  
  3. Update conversation state:
     └─ conversation_manager.update_state("1234567890", ConversationState.COLLECTING_NAME)
        ├─ conversation["state"] = "collecting_name"
        ├─ conversation["last_updated"] = "2025-11-23T18:50:05Z"
        └─ Log: "Updated state for 1234567890 to collecting_name"
  
  4. Return to webhook handler
     └─ Return {"status": "ok"}
```

### Phase 6: Customer Sends Name

```
Customer Action:
  └─ Receives bot message
  └─ Sends message: "John Doe"

WhatsApp → Server:
  └─ Same webhook flow as Phase 3
  └─ message_content = "john doe"

ChatbotEngine Processing:
  1. Get conversation for "1234567890"
     └─ Conversation exists with state = "collecting_name"
  
  2. Get current state:
     └─ current_state = ConversationState.COLLECTING_NAME
  
  3. Route to handler:
     └─ await _handle_name_input("1234567890", "john doe")
```

### Phase 7: State Handler - Name Input

```
_handle_name_input(customer_phone, message_content):
  1. Validate name:
     └─ if len("john doe") < 2:
        └─ Send error and return
     └─ Validation passes ✓
  
  2. Store name in conversation:
     └─ conversation_manager.update_data("1234567890", "name", "john doe")
        ├─ conversation["data"]["name"] = "john doe"
        ├─ conversation["last_updated"] = "2025-11-23T18:50:10Z"
        └─ Log: "Updated data for 1234567890: name = john doe"
  
  3. Send next prompt:
     └─ response = "Nice to meet you, John Doe! 😊\n\nPlease share your location..."
     └─ whatsapp_handler.send_text_message("1234567890", response)
  
  4. Update state:
     └─ conversation_manager.update_state("1234567890", ConversationState.COLLECTING_LOCATION)
        └─ state = "collecting_location"
```

### Phase 8: Customer Shares Location

```
Customer Action:
  └─ Taps location button in WhatsApp
  └─ Shares current location

WhatsApp Webhook:
  └─ message_type = "location"
  └─ Payload includes:
     {
       "location": {
         "latitude": 40.7128,
         "longitude": -74.0060
       }
     }

ChatbotEngine Processing:
  1. Get current state:
     └─ current_state = ConversationState.COLLECTING_LOCATION
  
  2. Route to handler:
     └─ await _handle_location_input("1234567890", message_data)
```

### Phase 9: State Handler - Location Input

```
_handle_location_input(customer_phone, message_data):
  1. Extract location:
     └─ raw_data = message_data["raw_data"]
     └─ location = raw_data["location"]
     └─ latitude = 40.7128
     └─ longitude = -74.0060
  
  2. Store location:
     └─ conversation_manager.update_data("1234567890", "location", {
          "latitude": 40.7128,
          "longitude": -74.0060
        })
  
  3. Send service options:
     └─ response = "Great! Location saved. 📍\n\nWhat service are you looking for?\n\n1. Hair Cutting\n2. Hair Coloring\n..."
     └─ whatsapp_handler.send_text_message("1234567890", response)
  
  4. Update state:
     └─ conversation_manager.update_state("1234567890", ConversationState.SELECTING_SERVICE)
```

### Phase 10: Customer Selects Service

```
Customer Action:
  └─ Sends message: "1"

ChatbotEngine Processing:
  1. Get current state:
     └─ current_state = ConversationState.SELECTING_SERVICE
  
  2. Route to handler:
     └─ await _handle_service_selection("1234567890", "1")
```

### Phase 11: State Handler - Service Selection

```
_handle_service_selection(customer_phone, message_content):
  1. Map selection to service:
     └─ services = {"1": "hair-cutting", "2": "hair-coloring", ...}
     └─ service_type = "hair-cutting"
  
  2. Validate:
     └─ if service_type not in services.values():
        └─ Send error and return
     └─ Validation passes ✓
  
  3. Store service:
     └─ conversation_manager.update_data("1234567890", "service_type", "hair-cutting")
  
  4. Search salons:
     └─ await _search_salons("1234567890", "hair-cutting")
```

### Phase 12: Search Salons (Backend Integration)

```
_search_salons(customer_phone, service_type):
  1. Get stored location:
     └─ location = conversation_manager.get_data("1234567890", "location")
        └─ {"latitude": 40.7128, "longitude": -74.0060}
  
  2. Prepare API payload:
     └─ payload = {
          "phone": "1234567890",
          "business": "salon",
          "action": "get-customer_booking_map",
          "service_name": "hair-cutting",
          "location": {"latitude": 40.7128, "longitude": -74.0060},
          "request_time": "2025-11-23T18:50:15Z"
        }
  
  3. Call backend API:
     └─ async with httpx.AsyncClient() as client:
        └─ response = await client.post(
             "http://localhost:8000/api/v1/getcustomerbookingmapping/hair-cutting/hair-cutting/1234567890",
             json=payload,
             timeout=10
           )
  
  4. Parse response:
     └─ result = response.json()
     └─ salons = result["result"]["response"]["salons"]
        └─ [
             {"salonName": "Beauty Bliss", "distance": 0.5},
             {"salonName": "Hair Haven", "distance": 1.2},
             ...
           ]
  
  5. Format salon list:
     └─ salon_list = "1. Beauty Bliss - 0.5km away\n2. Hair Haven - 1.2km away\n..."
  
  6. Send salon options:
     └─ response = "Found 5 salons! Here are the top 5:\n\n{salon_list}\n\nReply with number to select"
     └─ whatsapp_handler.send_text_message("1234567890", response)
  
  7. Update state:
     └─ conversation_manager.update_state("1234567890", ConversationState.VIEWING_SALON)
```

### Phase 13: Customer Selects Salon

```
Customer Action:
  └─ Sends message: "1"

ChatbotEngine Processing:
  1. Get current state:
     └─ current_state = ConversationState.VIEWING_SALON
  
  2. Route to handler:
     └─ await _handle_salon_selection("1234567890", "1")
```

### Phase 14: State Handler - Salon Selection

```
_handle_salon_selection(customer_phone, message_content):
  1. Parse selection:
     └─ salon_index = int("1") - 1 = 0
  
  2. Validate:
     └─ if salon_index < 0 or salon_index > 4:
        └─ Send error and return
     └─ Validation passes ✓
  
  3. Store selection:
     └─ conversation_manager.update_data("1234567890", "selected_salon_index", 0)
  
  4. Send time slots:
     └─ response = "Perfect! Now let's check available time slots.\n\nAvailable slots:\n\n1. 10:00 AM\n2. 11:00 AM\n..."
     └─ whatsapp_handler.send_text_message("1234567890", response)
  
  5. Update state:
     └─ conversation_manager.update_state("1234567890", ConversationState.SELECTING_SLOT)
```

### Phase 15: Customer Selects Time Slot

```
Customer Action:
  └─ Sends message: "2"

ChatbotEngine Processing:
  1. Get current state:
     └─ current_state = ConversationState.SELECTING_SLOT
  
  2. Route to handler:
     └─ await _handle_slot_selection("1234567890", "2")
```

### Phase 16: State Handler - Slot Selection

```
_handle_slot_selection(customer_phone, message_content):
  1. Parse selection:
     └─ slot_index = int("2") - 1 = 1
  
  2. Validate:
     └─ if slot_index < 0 or slot_index > 4:
        └─ Send error and return
     └─ Validation passes ✓
  
  3. Get slot time:
     └─ slots = ["10:00 AM", "11:00 AM", "2:00 PM", "3:00 PM", "4:00 PM"]
     └─ selected_slot = slots[1] = "11:00 AM"
  
  4. Store slot:
     └─ conversation_manager.update_data("1234567890", "selected_slot", "11:00 AM")
  
  5. Get booking details:
     └─ name = conversation_manager.get_data("1234567890", "name") = "john doe"
     └─ service = conversation_manager.get_data("1234567890", "service_type") = "hair-cutting"
  
  6. Show confirmation:
     └─ response = "Booking Summary:\n\n👤 Name: john doe\n🏢 Salon: Beauty Bliss\n💇 Service: Hair Cutting\n⏰ Time: 11:00 AM\n💰 Price: $25\n\nConfirm booking? (Yes/No)"
     └─ whatsapp_handler.send_text_message("1234567890", response)
  
  7. Update state:
     └─ conversation_manager.update_state("1234567890", ConversationState.CONFIRMING_BOOKING)
```

### Phase 17: Customer Confirms Booking

```
Customer Action:
  └─ Sends message: "Yes"

ChatbotEngine Processing:
  1. Get current state:
     └─ current_state = ConversationState.CONFIRMING_BOOKING
  
  2. Route to handler:
     └─ await _handle_booking_confirmation("1234567890", "yes")
```

### Phase 18: State Handler - Booking Confirmation

```
_handle_booking_confirmation(customer_phone, message_content):
  1. Check response:
     └─ if message_content in ["yes", "y"]:
        └─ await _create_booking("1234567890")
     └─ else if message_content in ["no", "n"]:
        └─ Send cancellation message
        └─ Reset conversation
```

### Phase 19: Create Booking (Backend Integration)

```
_create_booking(customer_phone):
  1. Get booking details:
     └─ name = conversation_manager.get_data("1234567890", "name") = "john doe"
     └─ service_type = conversation_manager.get_data("1234567890", "service_type") = "hair-cutting"
  
  2. Prepare API payload:
     └─ payload = {
          "phone": "1234567890",
          "name": "john doe",
          "business": "salon",
          "service_type": "hair-cutting",
          "action": "CREATE-BOOKING"
        }
  
  3. Call backend API:
     └─ async with httpx.AsyncClient() as client:
        └─ response = await client.post(
             "http://localhost:8000/api/v1/makerequest",
             json=payload,
             timeout=10
           )
  
  4. Parse response:
     └─ result = response.json()
     └─ status = result["result"]["status"]
  
  5. If SUCCESS:
     └─ response_text = "✅ Booking confirmed!\n\nYour appointment has been booked. You'll receive a confirmation shortly.\n\nThank you for using Salon Booking!"
     └─ whatsapp_handler.send_text_message("1234567890", response_text)
     └─ conversation_manager.update_state("1234567890", ConversationState.BOOKING_COMPLETE)
  
  6. If FAILED:
     └─ await _send_error_message("1234567890")
```

### Phase 20: Conversation Complete

```
Final State:
  └─ conversation["state"] = "booking_complete"
  └─ conversation["data"] = {
       "name": "john doe",
       "location": {"latitude": 40.7128, "longitude": -74.0060},
       "service_type": "hair-cutting",
       "selected_salon": "Beauty Bliss",
       "selected_slot": "11:00 AM",
       "booking_details": {...}
     }
  └─ conversation["message_count"] = 8

Customer receives:
  └─ ✅ Booking confirmed message
  └─ Booking details
  └─ Confirmation number (if provided by backend)
```

## Data Flow Summary

```
Customer Message
    ↓
WhatsApp Webhook
    ↓
Parse Message (WhatsAppHandler)
    ↓
Get/Create Conversation (ConversationManager)
    ↓
Get Current State
    ↓
Route to State Handler
    ↓
Process Input
    ↓
Update Conversation Data
    ↓
Call Backend API (if needed)
    ↓
Generate Response
    ↓
Send Message (WhatsAppHandler)
    ↓
Update State
    ↓
Return to Webhook Handler
    ↓
Customer Receives Message
```

## Error Handling Flow

```
If Error Occurs:
    ↓
Log Error with traceback
    ↓
Call _send_error_message(customer_phone)
    ↓
Send: "Sorry, something went wrong. Please try again later."
    ↓
Update state to ERROR
    ↓
Return error response to webhook
    ↓
Webhook returns {"status": "error", "message": error_msg}
```

## Conversation State Transitions

```
GREETING
    ↓ (user sends any message)
COLLECTING_NAME
    ↓ (user sends name)
COLLECTING_LOCATION
    ↓ (user shares location)
SELECTING_SERVICE
    ↓ (user selects service)
SEARCHING_SALONS
    ↓ (backend search completes)
VIEWING_SALON
    ↓ (user selects salon)
SELECTING_SLOT
    ↓ (user selects time slot)
CONFIRMING_BOOKING
    ↓ (user confirms)
BOOKING_COMPLETE
    ↓ (booking created)
[END]
```

## Memory Management

```
ConversationManager.conversations = {
  "1234567890": {
    "customer_phone": "1234567890",
    "state": "booking_complete",
    "created_at": "2025-11-23T18:50:00Z",
    "last_updated": "2025-11-23T18:50:45Z",
    "data": {...},
    "message_count": 8
  },
  "9876543210": {
    "customer_phone": "9876543210",
    "state": "collecting_name",
    "created_at": "2025-11-23T18:51:00Z",
    "last_updated": "2025-11-23T18:51:10Z",
    "data": {...},
    "message_count": 2
  }
}
```

All conversations stored in memory. Can be reset via API endpoint.
