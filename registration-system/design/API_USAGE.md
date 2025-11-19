# Salon Prototype 2 - API Usage Guide

## Overview
The API uses FastAPI with async request handling. All requests are queued and processed asynchronously through the pipeline. Users receive a `session_id` immediately and can poll for results.

## Main Endpoint

### POST `/api/v1/makerequest`
Universal entry point that routes requests based on the `action` field.

**Request Body:**
```json
{
  "action": "create-customer",
  "phone": "9876543210",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "session_id": "uuid-xxx",
  "status": "QUEUED",
  "message": "Request queued for processing. Use session_id to poll for results."
}
```

## Specific Endpoints

### 1. Create Customer
**POST `/v1/createcustomer`**

Request:
```json
{
  "phone": "9876543210",
  "name": "John Doe"
}
```

### 2. Update Customer
**POST `/v1/updatecustomer`**

Request:
```json
{
  "phone": "9876543210",
  "updates": {
    "name": "Jane Doe",
    "email": "jane@example.com"
  }
}
```

### 3. Delete Customer
**POST `/v1/deletecustomer`**

Request:
```json
{
  "phone": "9876543210"
}
```

### 4. Create Client (Salon)
**POST `/v1/createclient`**

Request:
```json
{
  "phone": "9876543210",
  "owner_name": "John Doe",
  "salon_name": "John's Salon",
  "service_type": "Hair Cutting",
  "working_hours": [
    {"day": "Monday", "open": "09:00", "close": "18:00"},
    {"day": "Tuesday", "open": "09:00", "close": "18:00"}
  ]
}
```

## Polling for Results

### GET `/session/{session_id}`
Poll for session results and execution status.

**Response:**
```json
{
  "session_id": "uuid-xxx",
  "phone": "9876543210",
  "status": "PERSISTED",
  "seq_id": 1,
  "version": 1,
  "data": {
    "phone": "9876543210",
    "name": "John Doe"
  },
  "phases": {
    "load": {
      "status": "LOADED",
      "timestamp": "2024-11-16T10:30:00"
    },
    "cache": {
      "status": "CACHED",
      "timestamp": "2024-11-16T10:30:01"
    },
    "validate": {
      "status": "VALIDATED",
      "timestamp": "2024-11-16T10:30:02",
      "errors": []
    },
    "process": {
      "status": "PROCESSED",
      "timestamp": "2024-11-16T10:30:03",
      "result": {
        "api_call": {"status": "API_SUCCESS"},
        "action": {"status": "SUCCESS", "result": {...}},
        "post_actions": [...]
      }
    },
    "persist": {
      "status": "PERSISTED",
      "timestamp": "2024-11-16T10:30:04",
      "result": {"filepath": "..."}
    }
  },
  "errors": []
}
```

## Health Check

### GET `/health`
Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "Salon Prototype 2"
}
```

## Request Flow

1. **User sends request** to `/api/v1/makerequest` or specific endpoint
2. **Immediate response** with `session_id` (non-blocking)
3. **Request queued** for async processing
4. **Background processing** through 5-phase pipeline:
   - Load: Initialize session
   - Cache: Store data
   - Validate: Validate against schema
   - Process: Execute business logic
   - Persist: Write to storage
5. **User polls** `/session/{session_id}` for results
6. **Final response** contains complete execution history

## Action Types

Valid actions for `/api/v1/makerequest`:
- `create-customer` → Routes to `/v1/createcustomer`
- `update-customer` → Routes to `/v1/updatecustomer`
- `delete-customer` → Routes to `/v1/deletecustomer`
- `create-client` → Routes to `/v1/createclient`
- `update-client` → Routes to `/v1/updateclient`
- `delete-client` → Routes to `/v1/deleteclient`

## Running the Server

```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Or directly:
```bash
python src/main.py
```

## Error Handling

All errors return appropriate HTTP status codes:
- `400`: Bad request (validation error, missing fields)
- `404`: Session not found
- `500`: Server error

Error response:
```json
{
  "detail": "Error message describing what went wrong"
}
```
