# Payload Data Field - Request Data Storage

## Overview

Added a `data` field to the `MainRequest` model to store consolidated request data. This field is populated in `route_salon_request()` with all request fields, making it easily accessible to handlers.

## Changes Made

### 1. MainRequest Model Update

**Location:** `src/checkbusiness.py`

**Before:**
```python
class MainRequest(BaseModel):
    """Main request payload"""
    action: str
    phone: str
    business: str
    name: Optional[str] = None
    updates: Optional[Dict[str, Any]] = None
    owner_name: Optional[str] = None
    salon_name: Optional[str] = None
    service_type: Optional[str] = None
    working_hours: Optional[list] = None
```

**After:**
```python
class MainRequest(BaseModel):
    """Main request payload"""
    action: str
    phone: str
    business: str
    name: Optional[str] = None
    updates: Optional[Dict[str, Any]] = None
    owner_name: Optional[str] = None
    salon_name: Optional[str] = None
    service_type: Optional[str] = None
    working_hours: Optional[list] = None
    data: Optional[Dict[str, Any]] = None  # Request data storage
```

### 2. Salon API Update

**Location:** `src/business/salon/api.py` - `route_salon_request()`

**Added Code:**
```python
# Populate data field in payload with request data
payload.data = {
    "phone": payload.phone,
    "name": payload.name or "",
    "business": payload.business,
    "updates": payload.updates or {},
    "owner_name": payload.owner_name or "",
    "salon_name": payload.salon_name or "",
    "service_type": payload.service_type or "",
    "working_hours": payload.working_hours or []
}
logger.info(f"Populated payload.data with request fields")
```

## Data Field Structure

```python
payload.data = {
    "phone": "9876543210",
    "name": "John Doe",
    "business": "salon",
    "updates": {"email": "john@example.com"},
    "owner_name": "John Smith",
    "salon_name": "Beauty Salon XYZ",
    "service_type": "hair_cutting",
    "working_hours": [{"day": "Monday", "open": "09:00", "close": "18:00"}]
}
```

## Usage in Handlers

### Before (Without data field)
```python
async def create_customer(payload, background_tasks, business_context, entity_context, session):
    # Access individual fields from payload
    phone = payload.phone
    name = payload.name
    business = payload.business
```

### After (With data field)
```python
async def create_customer(payload, background_tasks, business_context, entity_context, session):
    # Option 1: Access from data field
    phone = payload.data["phone"]
    name = payload.data["name"]
    
    # Option 2: Access individual fields (still available)
    phone = payload.phone
    name = payload.name
    
    # Option 3: Use entire data dict
    data = payload.data
    customer_record = entity_context.customer_manager.create_customer(**data)
```

## Payload Structure After route_salon_request

```python
{
    # Original fields
    "action": "create-customer",
    "phone": "9876543210",
    "business": "salon",
    "name": "John Doe",
    "updates": None,
    "owner_name": None,
    "salon_name": None,
    "service_type": None,
    "working_hours": None,
    
    # Added by route_salon_request
    "session_id": "uuid-1",
    "seq_id": 1,
    "version": 1,
    
    # New data field
    "data": {
        "phone": "9876543210",
        "name": "John Doe",
        "business": "salon",
        "updates": {},
        "owner_name": "",
        "salon_name": "",
        "service_type": "",
        "working_hours": []
    }
}
```

## Flow Diagram

```
HTTP Request
  │
  ├─ FastAPI parses to MakeRequestPayload
  │
  ├─ Converted to dict: payload.dict()
  │
  ├─ Validated and converted to MainRequest
  │
  ├─ route_salon_request(payload, ...)
  │  │
  │  ├─ Create session
  │  │
  │  ├─ Populate payload.data with all fields
  │  │  ├─ phone
  │  │  ├─ name
  │  │  ├─ business
  │  │  ├─ updates
  │  │  ├─ owner_name
  │  │  ├─ salon_name
  │  │  ├─ service_type
  │  │  └─ working_hours
  │  │
  │  └─ Pass to handler
  │
  ├─ Handler receives payload with data field
  │
  └─ Handler uses payload.data for business logic
```

## Benefits

1. **Consolidated Data** - All request fields in one place
2. **Easy Access** - Handlers can access `payload.data` directly
3. **Backward Compatible** - Individual fields still available
4. **Flexible** - Can pass entire data dict to functions
5. **Cleaner Code** - No need to reconstruct data in handlers

## Default Values

Fields with None values are converted to defaults:

```python
"name": payload.name or ""              # Empty string if None
"updates": payload.updates or {}        # Empty dict if None
"owner_name": payload.owner_name or ""  # Empty string if None
"salon_name": payload.salon_name or ""  # Empty string if None
"service_type": payload.service_type or ""  # Empty string if None
"working_hours": payload.working_hours or []  # Empty list if None
```

## Example Requests and Resulting Data

### Example 1: Create Customer

**Request:**
```json
{
    "action": "create-customer",
    "phone": "9876543210",
    "business": "salon",
    "name": "John Doe"
}
```

**Resulting payload.data:**
```python
{
    "phone": "9876543210",
    "name": "John Doe",
    "business": "salon",
    "updates": {},
    "owner_name": "",
    "salon_name": "",
    "service_type": "",
    "working_hours": []
}
```

### Example 2: Update Customer

**Request:**
```json
{
    "action": "update-customer",
    "phone": "9876543210",
    "business": "salon",
    "updates": {
        "name": "Jane Doe",
        "email": "jane@example.com"
    }
}
```

**Resulting payload.data:**
```python
{
    "phone": "9876543210",
    "name": "",
    "business": "salon",
    "updates": {
        "name": "Jane Doe",
        "email": "jane@example.com"
    },
    "owner_name": "",
    "salon_name": "",
    "service_type": "",
    "working_hours": []
}
```

### Example 3: Create Client

**Request:**
```json
{
    "action": "create-client",
    "phone": "9876543210",
    "business": "salon",
    "owner_name": "John Smith",
    "salon_name": "Beauty Salon XYZ",
    "service_type": "hair_cutting",
    "working_hours": [
        {"day": "Monday", "open": "09:00", "close": "18:00"}
    ]
}
```

**Resulting payload.data:**
```python
{
    "phone": "9876543210",
    "name": "",
    "business": "salon",
    "updates": {},
    "owner_name": "John Smith",
    "salon_name": "Beauty Salon XYZ",
    "service_type": "hair_cutting",
    "working_hours": [
        {"day": "Monday", "open": "09:00", "close": "18:00"}
    ]
}
```

## Handler Implementation

### Using payload.data

```python
async def create_customer(payload, background_tasks, business_context, entity_context, session):
    """Create a new customer"""
    if not payload.phone or not payload.name or not payload.business:
        raise HTTPException(status_code=400, detail="phone, name, and business are required")
    
    try:
        logger.info(f"Creating customer with phone: {payload.phone}, session: {session['session_id']}")
        
        # Use data from payload.data
        data = payload.data
        
        # Create customer record
        customer_record = entity_context.customer_manager.create_customer(
            phone=data["phone"],
            name=data["name"],
            business=data["business"]
        )
        
        # Log operation
        log_operation(
            action="CREATE-CUSTOMER",
            phone=payload.phone,
            status="COMPLETED",
            session_id=session["session_id"],
            details={
                "seq_id": session.get("seq_id"),
                "version": session.get("version"),
                "customer_id": customer_record.get("customerId")
            }
        )
        
        return SessionResponse(
            session_id=session["session_id"],
            status="COMPLETED",
            message="Customer creation completed"
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Logging

```python
logger.info(f"Populated payload.data with request fields")
```

## Performance Impact

- **Minimal** - Simple dictionary creation
- **No Lock Overhead** - No cache access
- **In-Memory** - No file I/O

## Backward Compatibility

- **Fully Compatible** - Individual fields still available
- **Optional** - data field is optional (None if not populated)
- **No Breaking Changes** - Existing code continues to work

## Future Enhancements

1. **Data Validation** - Validate data field structure
2. **Data Transformation** - Transform data before storing
3. **Data Encryption** - Encrypt sensitive data
4. **Data Audit** - Track data changes
5. **Data Versioning** - Store data versions

## Summary

The `data` field in `MainRequest` provides a convenient way to access all request fields in one place. It's populated in `route_salon_request()` and available to all handlers, making the code cleaner and more maintainable.
