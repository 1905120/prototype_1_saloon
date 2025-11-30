# Step 2: Customer Record Management

## Overview
Step 2 focuses on managing customer records through the chatbot layer. This includes creating new customer records, retrieving existing customer information, updating customer details, and maintaining customer preferences.

## Scope
- **Create**: Register new customers via chatbot
- **Read**: Retrieve customer information
- **Update**: Modify existing customer details
- **Delete**: Soft delete customer records (if needed)
- **Search**: Find customers by phone, name, or other identifiers

## Customer Record Structure

### Customer Data Model
```json
{
  "customer_id": "phone_number",
  "phone": "string (10-15 digits)",
  "name": "string",
  "email": "string (optional)",
  "dateOfBirth": "string (YYYY-MM-DD, optional)",
  "address": "string (optional)",
  "location": {
    "latitude": "float",
    "longitude": "float"
  },
  "version": "integer",
  "action": "string (CREATE, UPDATE, DELETE)",
  "approvalStatus": "string (PENDING, APPROVED, REJECTED)",
  "registeredAt": "ISO 8601 timestamp",
  "updatedAt": "ISO 8601 timestamp (optional)",
  "updatedFields": "array of field names (optional)",
  "business": "salon",
  "service_type": "string (service preference)",
  "preferences": {
    "preferred_services": ["array of service types"],
    "preferred_salons": ["array of salon IDs"],
    "notification_preference": "SMS/WhatsApp/Email",
    "language": "string"
  },
  "booking_history": {
    "total_bookings": "integer",
    "last_booking_date": "ISO 8601 timestamp",
    "favorite_salon": "salon_id"
  }
}
```

## Chatbot Conversation Flows

### Flow 1: New Customer Registration

#### Step 1.1: Greeting & Identification
```
Bot: "Hi! Welcome to Salon Booking. What's your name?"
Customer: "John Doe"
Bot: "Nice to meet you, John! Is this your first time with us?"
Customer: "Yes"
```

#### Step 1.2: Collect Phone Number
```
Bot: "I see your WhatsApp number is +1-555-0123. Is this correct?"
Customer: "Yes"
Bot: "Great! I'll use this for all communications."
```

#### Step 1.3: Collect Email (Optional)
```
Bot: "Would you like to provide an email for booking confirmations? (Optional)"
Customer: "john@example.com"
Bot: "Perfect! Email saved."
```

#### Step 1.4: Collect Location
```
Bot: "Can you share your current location? This helps us find nearby salons."
Customer: [Shares location]
Bot: "Location saved! Latitude: 40.7128, Longitude: -74.0060"
```

#### Step 1.5: Collect Address (Optional)
```
Bot: "Would you like to save your home address? (Optional)"
Customer: "123 Main St, New York, NY 10001"
Bot: "Address saved!"
```

#### Step 1.6: Service Preference
```
Bot: "What services are you interested in?"
Bot: "1. Hair Cutting
2. Hair Coloring
3. Facial Treatment
4. Manicure
5. Pedicure
6. Massage Therapy
7. Other"
Customer: "1"
Bot: "Hair Cutting noted! Any other services?"
Customer: "No"
```

#### Step 1.7: Confirmation
```
Bot: "Let me confirm your details:
Name: John Doe
Phone: +1-555-0123
Email: john@example.com
Location: New York, NY
Services: Hair Cutting
Is everything correct? (Yes/No)"
Customer: "Yes"
Bot: "Welcome, John! Your profile is created. You're all set!"
```

### Flow 2: Returning Customer Greeting

#### Step 2.1: Recognition
```
Bot: "Hi John! Welcome back. Last visit: Nov 20, 2025 at Beauty Bliss"
Bot: "What can I help you with today?"
Bot: "1. Book an appointment
2. View my profile
3. View booking history
4. Update my details"
Customer: "2"
```

#### Step 2.2: Show Profile
```
Bot: "Here's your profile:
Name: John Doe
Phone: +1-555-0123
Email: john@example.com
Location: New York, NY
Services: Hair Cutting
Bookings: 5 total
Last booking: Nov 20, 2025"
```

### Flow 3: Update Customer Details

#### Step 3.1: Select Field to Update
```
Bot: "What would you like to update?"
Bot: "1. Name
2. Email
3. Address
4. Location
5. Service Preferences
6. Cancel"
Customer: "3"
```

#### Step 3.2: Update Address
```
Bot: "Current address: 123 Main St, New York, NY 10001"
Bot: "What's your new address?"
Customer: "456 Park Ave, New York, NY 10022"
Bot: "Address updated!"
```

#### Step 3.3: Confirmation
```
Bot: "Your profile has been updated. Updated fields: address
Changes saved at: 2025-11-23 18:50:00"
```

### Flow 4: Retrieve Customer Information

#### Step 4.1: Show All Details
```
Bot: "Here's your complete profile:
Name: John Doe
Phone: +1-555-0123
Email: john@example.com
Address: 456 Park Ave, New York, NY 10022
Location: 40.7689, -73.9776
Services: Hair Cutting
Registered: Nov 15, 2025
Last Updated: Nov 23, 2025"
```

## API Endpoints for Customer Management

### 1. Create Customer
```
POST /api/v1/chatbot/customer/create
Content-Type: application/json

Request:
{
  "phone": "5550123",
  "name": "John Doe",
  "email": "john@example.com",
  "address": "123 Main St, New York, NY 10001",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "service_type": "hair-cutting",
  "business": "salon",
  "action": "CREATE",
  "registeredAt": "2025-11-23T18:50:00Z"
}

Response:
{
  "result": {
    "response": {
      "customer_id": "5550123",
      "session_id": "uuid",
      "status": "SUCCESS",
      "message": "Customer created successfully"
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 2. Get Customer
```
GET /api/v1/chatbot/customer/{phone}

Response:
{
  "result": {
    "response": {
      "customer_id": "5550123",
      "phone": "5550123",
      "name": "John Doe",
      "email": "john@example.com",
      "address": "123 Main St, New York, NY 10001",
      "location": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "service_type": "hair-cutting",
      "version": 1,
      "registeredAt": "2025-11-23T18:50:00Z",
      "updatedAt": null,
      "preferences": {
        "preferred_services": ["hair-cutting"],
        "notification_preference": "WhatsApp"
      },
      "booking_history": {
        "total_bookings": 0,
        "last_booking_date": null
      }
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 3. Update Customer
```
PUT /api/v1/chatbot/customer/{phone}
Content-Type: application/json

Request:
{
  "name": "John Doe",
  "email": "newemail@example.com",
  "address": "456 Park Ave, New York, NY 10022",
  "updatedFields": ["email", "address"],
  "action": "UPDATE"
}

Response:
{
  "result": {
    "response": {
      "customer_id": "5550123",
      "status": "SUCCESS",
      "message": "Customer updated successfully",
      "updatedFields": ["email", "address"],
      "version": 2
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 4. Delete Customer (Soft Delete)
```
DELETE /api/v1/chatbot/customer/{phone}

Response:
{
  "result": {
    "response": {
      "customer_id": "5550123",
      "status": "SUCCESS",
      "message": "Customer deleted successfully"
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

### 5. Search Customers
```
GET /api/v1/chatbot/customer/search?name=John&phone=5550123

Response:
{
  "result": {
    "response": {
      "total_results": 1,
      "customers": [
        {
          "customer_id": "5550123",
          "name": "John Doe",
          "phone": "5550123",
          "email": "john@example.com",
          "registeredAt": "2025-11-23T18:50:00Z"
        }
      ]
    },
    "status": "SUCCESS"
  },
  "err_details": {}
}
```

## Data Validation Rules

### Phone Number
- Required field
- Format: 10-15 digits
- Must be unique
- Validation: `^\d{10,15}$`

### Name
- Required field
- Length: 2-100 characters
- Allowed characters: Letters, spaces, hyphens, apostrophes
- Validation: `^[a-zA-Z\s\-']{2,100}$`

### Email
- Optional field
- Valid email format
- Validation: Standard email regex

### Address
- Optional field
- Length: 5-200 characters
- Can contain letters, numbers, spaces, commas, periods, hyphens

### Location
- Optional field
- Latitude: -90 to 90
- Longitude: -180 to 180
- Both required if location is provided

### Service Type
- Required field
- Allowed values: hair-cutting, hair-coloring, hair-styling, facial-treatment, manicure, pedicure, massage-therapy, waxing

## Error Handling

### Common Errors

#### 1. Invalid Phone Number
```
{
  "result": {
    "response": {},
    "status": "FAILED",
    "message": "Invalid phone number format"
  },
  "err_details": {
    "err_msg": "Phone must be 10-15 digits",
    "err_type": "VALIDATION-ERROR",
    "field": "phone"
  }
}
```

#### 2. Duplicate Customer
```
{
  "result": {
    "response": {},
    "status": "FAILED",
    "message": "Customer already exists"
  },
  "err_details": {
    "err_msg": "Phone number already registered",
    "err_type": "DUPLICATE-ERROR",
    "existing_customer_id": "5550123"
  }
}
```

#### 3. Customer Not Found
```
{
  "result": {
    "response": {},
    "status": "FAILED",
    "message": "Customer not found"
  },
  "err_details": {
    "err_msg": "No customer found with phone: 5550123",
    "err_type": "NOT-FOUND-ERROR"
  }
}
```

#### 4. Missing Required Fields
```
{
  "result": {
    "response": {},
    "status": "FAILED",
    "message": "Missing required fields"
  },
  "err_details": {
    "err_msg": "Required fields missing: name, service_type",
    "err_type": "VALIDATION-ERROR",
    "missing_fields": ["name", "service_type"]
  }
}
```

## File Storage Structure

### Customer Records Location
```
data/businesses/salon/Customer/live/
├── {phone}#salon#{version}.json
├── 5550123#salon#1.json
├── 5550123#salon#2.json (after update)
└── ...
```

### Customer Metadata
```
data/businesses/salon/meta_data/
├── customer_metadata.json
└── customer_booking_map.json
```

## Testing Scenarios

### Test 1: Create 10 New Customers
- Create 10 unique customer records via chatbot
- Verify all records stored in `Customer/live/`
- Verify metadata updated in `customer_metadata.json`
- Verify version tracking (all should be version 1)

### Test 2: Update Customer Details
- Update 5 customers with new information
- Verify version incremented to 2
- Verify `updatedFields` tracked correctly
- Verify `updatedAt` timestamp recorded

### Test 3: Retrieve Customer Information
- Retrieve each created customer
- Verify all fields match stored data
- Test search by phone and name

### Test 4: Error Handling
- Test invalid phone numbers
- Test duplicate phone numbers
- Test missing required fields
- Test invalid email formats

### Test 5: Data Persistence
- Verify data persists across server restarts
- Verify metadata consistency
- Verify version history maintained

## Success Criteria
- All customer records created successfully
- All data validated before storage
- All records retrievable by phone number
- Updates tracked with version numbers
- Error messages clear and actionable
- 100% data persistence
- Response time < 2 seconds for all operations
