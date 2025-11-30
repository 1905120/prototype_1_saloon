# Business Numbers Configuration

## Overview
Business numbers are WhatsApp phone numbers through which customers can reach the chatbot to search and book salon appointments. Each business number can have different configurations, features, and settings.

## Business Number Structure

```json
{
  "number_id": "salon_main",
  "phone_id": "your_phone_id",
  "phone_number": "+1-555-0100",
  "display_name": "Salon Booking",
  "business_name": "Salon Booking System",
  "description": "Book salon appointments online",
  "status": "active",
  "created_at": "2025-11-23T18:50:00Z",
  "updated_at": "2025-11-23T18:50:00Z",
  "features": ["booking", "search", "notifications"],
  "supported_languages": ["en"],
  "timezone": "UTC"
}
```

## API Endpoints

### 1. Get All Business Numbers
```
GET /v1/chatbot/business-numbers/

Response:
{
  "result": {
    "response": {
      "total_numbers": 2,
      "business_numbers": {
        "salon_main": {...},
        "salon_secondary": {...}
      }
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 2. Get Active Business Numbers
```
GET /v1/chatbot/business-numbers/active

Response:
{
  "result": {
    "response": {
      "total_active": 1,
      "business_numbers": [
        {
          "number_id": "salon_main",
          "phone_number": "+1-555-0100",
          "status": "active",
          ...
        }
      ]
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 3. Get Specific Business Number
```
GET /v1/chatbot/business-numbers/{number_id}

Example:
GET /v1/chatbot/business-numbers/salon_main

Response:
{
  "result": {
    "response": {
      "number_id": "salon_main",
      "phone_number": "+1-555-0100",
      "display_name": "Salon Booking",
      "status": "active",
      ...
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 4. Create Business Number
```
POST /v1/chatbot/business-numbers/

Request:
{
  "number_id": "salon_main",
  "phone_id": "your_phone_id",
  "phone_number": "+1-555-0100",
  "display_name": "Salon Booking",
  "business_name": "Salon Booking System",
  "description": "Book salon appointments online",
  "features": ["booking", "search", "notifications"],
  "supported_languages": ["en"],
  "timezone": "UTC"
}

Response:
{
  "result": {
    "response": {
      "number_id": "salon_main",
      "data": {...},
      "message": "Business number created successfully"
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 5. Update Business Number
```
PUT /v1/chatbot/business-numbers/{number_id}

Example:
PUT /v1/chatbot/business-numbers/salon_main

Request:
{
  "display_name": "Updated Salon Booking",
  "description": "Updated description"
}

Response:
{
  "result": {
    "response": {
      "number_id": "salon_main",
      "data": {...},
      "message": "Business number updated successfully"
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 6. Delete Business Number
```
DELETE /v1/chatbot/business-numbers/{number_id}

Example:
DELETE /v1/chatbot/business-numbers/salon_main

Response:
{
  "result": {
    "response": {
      "number_id": "salon_main",
      "message": "Business number deleted successfully"
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 7. Update Business Number Status
```
PATCH /v1/chatbot/business-numbers/{number_id}/status

Example:
PATCH /v1/chatbot/business-numbers/salon_main/status

Request:
{
  "status": "active"
}

Valid statuses: "active", "inactive", "suspended"

Response:
{
  "result": {
    "response": {
      "number_id": "salon_main",
      "status": "active",
      "data": {...}
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 8. Add Feature to Business Number
```
POST /v1/chatbot/business-numbers/{number_id}/features/{feature}

Example:
POST /v1/chatbot/business-numbers/salon_main/features/notifications

Response:
{
  "result": {
    "response": {
      "number_id": "salon_main",
      "feature": "notifications",
      "data": {...}
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 9. Remove Feature from Business Number
```
DELETE /v1/chatbot/business-numbers/{number_id}/features/{feature}

Example:
DELETE /v1/chatbot/business-numbers/salon_main/features/notifications

Response:
{
  "result": {
    "response": {
      "number_id": "salon_main",
      "feature": "notifications",
      "data": {...}
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

## Available Features

- **booking**: Allow customers to book appointments
- **search**: Allow customers to search for salons
- **notifications**: Send appointment reminders and updates
- **history**: Show booking history
- **support**: Customer support chat
- **payments**: Process payments
- **ratings**: Allow customers to rate salons

## Configuration File Location

Business numbers are stored in: `data/chatbot/business_numbers.json`

## Default Configuration

When the system starts, a default business number is created:

```json
{
  "business_numbers": {
    "salon_main": {
      "phone_id": "your_phone_id",
      "phone_number": "+1-555-0100",
      "display_name": "Salon Booking",
      "business_name": "Salon Booking System",
      "description": "Book salon appointments online",
      "status": "active",
      "created_at": "2025-11-23T18:50:00Z",
      "features": ["booking", "search", "notifications"],
      "supported_languages": ["en"],
      "timezone": "UTC"
    }
  }
}
```

## Usage Examples

### Example 1: Create a New Business Number
```bash
curl -X POST http://localhost:8000/v1/chatbot/business-numbers/ \
  -H "Content-Type: application/json" \
  -d '{
    "number_id": "salon_secondary",
    "phone_id": "secondary_phone_id",
    "phone_number": "+1-555-0101",
    "display_name": "Salon Booking - Secondary",
    "business_name": "Salon Booking System",
    "description": "Secondary booking channel",
    "features": ["booking", "search"],
    "supported_languages": ["en", "es"],
    "timezone": "EST"
  }'
```

### Example 2: Get All Active Numbers
```bash
curl -X GET http://localhost:8000/v1/chatbot/business-numbers/active
```

### Example 3: Update Number Status
```bash
curl -X PATCH http://localhost:8000/v1/chatbot/business-numbers/salon_main/status \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'
```

### Example 4: Add Feature
```bash
curl -X POST http://localhost:8000/v1/chatbot/business-numbers/salon_main/features/ratings
```

## Customer Interaction Flow

1. Customer saves business number in WhatsApp contacts
2. Customer sends message to business number
3. Chatbot receives message via webhook
4. Chatbot processes message and responds
5. Customer can search salons and make bookings

## Multi-Channel Support

Multiple business numbers can be configured for:
- Different regions/cities
- Different languages
- Different business units
- Load balancing
- Redundancy

Each number operates independently with its own configuration and features.

## Monitoring

Monitor business numbers through:
- `GET /v1/chatbot/business-numbers/` - View all numbers
- `GET /v1/chatbot/business-numbers/active` - View active numbers
- Check `data/chatbot/business_numbers.json` for configuration

## Best Practices

1. **Always have at least one active business number**
2. **Use descriptive display names** for customer recognition
3. **Enable notifications feature** for better customer experience
4. **Monitor number status** regularly
5. **Keep phone IDs and access tokens secure**
6. **Test new numbers before making them active**
7. **Document custom features** for your team
