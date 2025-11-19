# Operation Data Fields - Source and Mapping

## Overview

The `operation_data` dictionary in `route_salon_request` is constructed from the `MainRequest` payload. This document explains where each field comes from and how they are mapped.

## MainRequest Model

**Source:** `src/checkbusiness.py`

```python
class MainRequest(BaseModel):
    """Main request payload"""
    phone: str                               # Required
    business: str                            # Required
    name: Optional[str] = None               # Optional
    updates: Optional[Dict[str, Any]] = None # Optional
    owner_name: Optional[str] = None         # Optional
    salon_name: Optional[str] = None         # Optional
    service_type: Optional[str] = None       # Optional
    working_hours: Optional[list] = None     # Optional
```

## Operation Data Construction

**Location:** `src/business/salon/api.py` - `route_salon_request()` function

```python
operation_data = {
    "phone": payload.phone,
    "name": payload.name or "",
    "business": payload.business,
    "updates": payload.updates or {},
    "owner_name": payload.owner_name or "",
    "salon_name": payload.salon_name or "",
    "service_type": payload.service_type or "",
    "working_hours": payload.working_hours or []
}
```

## Field Mapping

### 1. phone
**Source:** `payload.phone`
**Type:** `str`
**Required:** Yes
**Description:** Customer/client phone number
**Example:** `"9876543210"`

### 2. name
**Source:** `payload.name or ""`
**Type:** `str`
**Required:** No (defaults to empty string)
**Description:** Customer name
**Example:** `"John Doe"`
**Used for:** Customer creation/update

### 3. business
**Source:** `payload.business`
**Type:** `str`
**Required:** Yes
**Description:** Business type (currently only "salon")
**Example:** `"salon"`

### 4. updates
**Source:** `payload.updates or {}`
**Type:** `Dict[str, Any]`
**Required:** No (defaults to empty dict)
**Description:** Fields to update for UPDATE operations
**Example:** `{"name": "Jane Doe", "email": "jane@example.com"}`
**Used for:** UPDATE-CUSTOMER, UPDATE-CLIENT operations

### 5. owner_name
**Source:** `payload.owner_name or ""`
**Type:** `str`
**Required:** No (defaults to empty string)
**Description:** Salon owner name
**Example:** `"John Smith"`
**Used for:** Client (salon) creation/update

### 6. salon_name
**Source:** `payload.salon_name or ""`
**Type:** `str`
**Required:** No (defaults to empty string)
**Description:** Salon business name
**Example:** `"Beauty Salon XYZ"`
**Used for:** Client (salon) creation/update

### 7. service_type
**Source:** `payload.service_type or ""`
**Type:** `str`
**Required:** No (defaults to empty string)
**Description:** Type of services offered by salon
**Example:** `"hair_cutting"` or `"beauty_services"`
**Used for:** Client (salon) creation/update

### 8. working_hours
**Source:** `payload.working_hours or []`
**Type:** `list`
**Required:** No (defaults to empty list)
**Description:** Salon working hours schedule
**Example:** `[{"day": "Monday", "open": "09:00", "close": "18:00"}]`
**Used for:** Client (salon) creation/update

## Request Flow

```
HTTP Request
  ↓
FastAPI Endpoint (main.py)
  ↓
make_request(payload: MakeRequestPayload)
  ↓
check_and_route_business(payload.dict())
  ↓
MainRequest(**payload)
  ↓
route_salon_request(payload, background_tasks, business_context, entity_context)
  ↓
operation_data = {
    "phone": payload.phone,
    "name": payload.name or "",
    ...
}
  ↓
SessionManager.load_session(phone, operation_data, task, operation_type)
  ↓
Session object with operation_data stored
```

## Usage in Session

The `operation_data` is stored in the session object:

```python
session = {
    "session_id": "uuid",
    "phone": "9876543210",
    "operation_type": "CREATE",
    "status": "LOADED",
    "created_at": "2024-11-17T...",
    "data": operation_data,  # <-- Stored here
    "seq_id": 1,
    "version": 1,
    "metadata": {...}
}
```

## Usage in Handlers

Handlers receive the session and can access operation_data:

```python
async def create_customer(payload, background_tasks, business_context, entity_context, session):
    # Access operation_data from session
    operation_data = session["data"]
    
    # Use fields
    phone = operation_data["phone"]
    name = operation_data["name"]
    business = operation_data["business"]
    
    # Create customer record
    customer_record = entity_context.customer_manager.create_customer(
        phone=phone,
        name=name,
        business=business
    )
```

## Example Requests

### Create Customer Request
```json
{
    "action": "create-customer",
    "phone": "9876543210",
    "business": "salon",
    "name": "John Doe"
}
```

**Resulting operation_data:**
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

### Update Customer Request
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

**Resulting operation_data:**
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

### Create Client Request
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

**Resulting operation_data:**
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

## Default Values

Fields with default values use the `or` operator:

```python
"name": payload.name or ""              # Empty string if None
"updates": payload.updates or {}        # Empty dict if None
"owner_name": payload.owner_name or ""  # Empty string if None
"salon_name": payload.salon_name or ""  # Empty string if None
"service_type": payload.service_type or ""  # Empty string if None
"working_hours": payload.working_hours or []  # Empty list if None
```

## Validation

### Required Fields
- `action` - Validated in route_salon_request
- `phone` - Validated in route_salon_request
- `business` - Validated in check_business()

### Optional Fields
- All other fields are optional
- Defaults provided if not supplied
- Handlers validate as needed

## Data Flow Summary

```
HTTP Request JSON
  ↓
FastAPI parses to MakeRequestPayload
  ↓
Converted to dict: payload.dict()
  ↓
Validated and converted to MainRequest
  ↓
Fields extracted to operation_data dict
  ↓
Passed to SessionManager.load_session()
  ↓
Stored in session["data"]
  ↓
Passed to handlers via session parameter
  ↓
Handlers use operation_data for business logic
```

## Future Enhancements

1. **Validation** - Add Pydantic validators for field formats
2. **Transformation** - Transform fields before storing (e.g., normalize phone)
3. **Enrichment** - Add computed fields (e.g., timestamp)
4. **Filtering** - Remove sensitive fields before logging
5. **Versioning** - Support different payload versions
