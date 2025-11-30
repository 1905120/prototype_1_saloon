# Chatbot Layer Requirements

## Overview
The chatbot layer is a conversational interface that handles multiple interactions between the system and customers through WhatsApp. It collects customer details, manages booking workflows, and provides salon information through natural conversation.

## Integration Points

### 1. WhatsApp API Integration
- **Provider**: WhatsApp Business API (Meta/Facebook)
- **Purpose**: Send and receive messages to/from customers
- **Key Features**:
  - Receive incoming customer messages
  - Send outgoing messages with text, media, and templates
  - Handle message delivery and read receipts
  - Webhook for receiving incoming messages
  - Rate limiting and message queuing

### 2. System API Integration
- **Salon API** (`/api/v1/makerequest`): Create/update customer and client records
- **Booking API**: Get salon suggestions, check availability, create bookings
- **Customer API**: Retrieve customer history, preferences, location
- **Payment API**: Process payments for bookings

## Core Functionalities

### 1. Customer Information Collection
The chatbot should collect the following details through conversational flow:

#### Initial Registration (New Customers)
- **Name**: Customer's full name
- **Phone**: Phone number (already available from WhatsApp)
- **Email**: Email address (optional)
- **Location**: Current location (latitude, longitude)
- **Address**: Residential address (optional)
- **Service Preference**: Type of service interested in (hair, beauty, spa, etc.)

#### Returning Customers
- Retrieve stored information from system
- Update preferences if needed
- Show booking history

### 2. Salon Discovery & Browsing
- **Nearby Salons**: Show salons within 2km radius based on customer location
- **Salon Details**: 
  - Name, address, phone
  - Services offered
  - Operating hours
  - Available time slots
  - Pricing information
  - Customer ratings/reviews
- **Search**: Allow customers to search by service type, salon name, or location
- **Filters**: Filter by service, price range, availability

### 3. Booking Management
- **Slot Selection**: Guide customer through available time slots
- **Booking Confirmation**: Confirm booking details before submission
- **Approval Workflow**: 
  - If salon requires approval: Notify customer of pending approval
  - If auto-approved: Confirm booking immediately
- **Payment Processing**:
  - Online payment option
  - Cash payment option
  - Payment status updates

### 4. Conversation Flow Management
- **State Management**: Track conversation state (collecting name, selecting salon, choosing slot, etc.)
- **Context Preservation**: Maintain conversation context across multiple messages
- **Error Handling**: Handle invalid inputs gracefully with re-prompts
- **Fallback Responses**: Handle out-of-scope questions with helpful redirects

### 5. Message Types & Templates

#### Text Messages
- Greetings and introductions
- Information requests
- Confirmations
- Error messages
- Help/FAQ responses

#### Interactive Messages
- Quick reply buttons (Yes/No, Multiple choice)
- List selections (Salon list, Service list, Time slots)
- Location sharing requests

#### Media Messages
- Salon images/photos
- Service images
- Receipts/confirmations (PDF)

#### Template Messages
- Booking confirmation
- Payment receipt
- Appointment reminders
- Cancellation notices

### 6. Customer Support Features
- **FAQ Handling**: Answer common questions about services, pricing, policies
- **Booking History**: Show past bookings and allow rebooking
- **Cancellation**: Allow customers to cancel bookings
- **Rescheduling**: Modify existing bookings
- **Support Escalation**: Escalate to human agent if needed

### 7. Notifications & Reminders
- **Booking Confirmation**: Send confirmation after booking
- **Appointment Reminders**: Send reminders 24 hours before appointment
- **Status Updates**: Notify about approval/rejection of bookings
- **Payment Reminders**: Remind about pending payments

## Technical Requirements

### 1. Architecture
- **Modular Design**: Separate concerns (message handling, conversation logic, API integration)
- **Stateless Processing**: Handle messages independently with state stored externally
- **Async Processing**: Handle multiple concurrent conversations
- **Queue-based**: Use message queue for reliable message processing

### 2. Data Storage
- **Conversation State**: Store active conversation state per customer
- **Session Management**: Track session duration and context
- **Message History**: Log all messages for audit and analytics
- **Customer Preferences**: Cache customer preferences for quick access

### 3. API Endpoints Required

#### Incoming Messages
```
POST /api/v1/chatbot/webhook
- Receive messages from WhatsApp
- Validate webhook signature
- Queue message for processing
```

#### Outgoing Messages
```
POST /api/v1/chatbot/send-message
- Send message to customer via WhatsApp
- Handle message templates
- Track delivery status
```

#### Conversation Management
```
GET /api/v1/chatbot/conversation/{customer_id}
POST /api/v1/chatbot/conversation/{customer_id}/reset
GET /api/v1/chatbot/messages/{customer_id}
```

#### Analytics
```
GET /api/v1/chatbot/analytics/conversations
GET /api/v1/chatbot/analytics/messages
GET /api/v1/chatbot/analytics/bookings-via-chatbot
```

### 4. Error Handling
- **Message Delivery Failures**: Retry with exponential backoff
- **API Timeouts**: Graceful degradation with user-friendly messages
- **Invalid Inputs**: Validate and re-prompt for correct format
- **Rate Limiting**: Handle WhatsApp API rate limits
- **Webhook Failures**: Implement retry mechanism for failed webhooks

### 5. Security & Compliance
- **Webhook Signature Verification**: Validate all incoming webhooks
- **Data Encryption**: Encrypt sensitive customer data
- **PII Protection**: Handle personal information securely
- **Access Control**: Authenticate API requests
- **Audit Logging**: Log all interactions for compliance

## Conversation Flow Examples

### Example 1: New Customer Booking
```
Bot: "Hi! Welcome to Salon Booking. What's your name?"
Customer: "John"
Bot: "Nice to meet you, John! What service are you looking for?"
Customer: "Hair cutting"
Bot: "Great! I found 5 salons near you offering hair cutting. Here are the top 3:
1. Beauty Bliss - 0.5km away
2. Hair Haven - 1.2km away
3. Glamour Studio - 1.8km away
Which one interests you?"
Customer: "Beauty Bliss"
Bot: "Perfect! Beauty Bliss has the following slots available today:
1. 10:00 AM
2. 11:00 AM
3. 2:00 PM
Which time works for you?"
Customer: "11:00 AM"
Bot: "Confirming your booking:
Salon: Beauty Bliss
Service: Hair Cutting
Date: Today
Time: 11:00 AM
Price: $25
Proceed? (Yes/No)"
Customer: "Yes"
Bot: "Great! Your booking is confirmed. Confirmation details sent to your email."
```

### Example 2: Returning Customer Quick Booking
```
Bot: "Hi John! Welcome back. Your last visit was at Beauty Bliss on Nov 20.
Would you like to book the same service? (Yes/No)"
Customer: "Yes"
Bot: "Available slots at Beauty Bliss for Hair Cutting:
1. Tomorrow 10:00 AM
2. Tomorrow 2:00 PM
3. Day after 11:00 AM
Which slot?"
Customer: "Tomorrow 10:00 AM"
Bot: "Booking confirmed for tomorrow at 10:00 AM. See you then!"
```

## Performance Requirements
- **Message Response Time**: < 2 seconds for simple responses
- **Booking Confirmation**: < 5 seconds end-to-end
- **Concurrent Conversations**: Support 1000+ concurrent active conversations
- **Message Throughput**: Handle 10,000+ messages per hour
- **Uptime**: 99.5% availability

## Monitoring & Analytics
- **Conversation Metrics**: Total conversations, average duration, completion rate
- **Message Metrics**: Total messages, delivery rate, error rate
- **Booking Metrics**: Bookings initiated via chatbot, conversion rate, average booking value
- **User Satisfaction**: Track user feedback and satisfaction scores
- **Error Tracking**: Monitor and alert on errors and failures

## Future Enhancements
- **AI/ML Integration**: Natural language understanding for better intent detection
- **Multi-language Support**: Support multiple languages
- **Voice Messages**: Handle voice message transcription
- **Payment Integration**: Direct payment processing via WhatsApp
- **Proactive Notifications**: Send personalized offers and recommendations
- **Integration with CRM**: Sync customer data with CRM systems
