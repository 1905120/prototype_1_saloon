# Session Load Simplified - Removed Data Parameter

## Overview

Simplified `SessionManager.load_session()` by removing the `data` parameter. The method now focuses solely on session creation and seq_id/version generation. Request data is handled separately in the handlers.

## Changes Made

### SessionManager.load_session() Signature

**Before:**
```python
def load_session(self, phone: str, data: Dict[str, Any], 
                task: str, operation_type: OperationType) -> Dict[str, Any]:
```

**After:**
```python
def load_session(self, phone: str, task: str, operation_type: OperationType) -> Dict[str, Any]:
```

### Removed Code

**Before:**
```python
# Prepare data for session loading
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

# Load session with seq_id and version using shared cache
session = entity_session_manager.load_session(
    phone=payload.phone,
    data=operation_data,
    task=payload.action,
    operation_type=operation_type
)

# ... in load_session ...
session["data"] = data
```

**After:**
```python
# Load session with seq_id and version using shared cache
session = entity_session_manager.load_session(
    phone=payload.phone,
    task=payload.action,
    operation_type=operation_type
)

# ... in load_session ...
# No session["data"] assignment
```

## Rationale

1. **Separation of Concerns** - Session management should focus on seq_id and version generation
2. **Data Handling** - Request data is already available in handlers via payload
3. **Simplicity** - Reduces method complexity and parameters
4. **Flexibility** - Handlers can decide how to use request data

## Session Object Structure

### Before
```python
{
    "session_id": "uuid",
    "phone": "9876543210",
    "operation_type": "CREATE",
    "status": "LOADED",
    "created_at": "2024-11-17T...",
    "data": {...},              # ← Removed
    "validation_errors": [],
    "process_result": None,
    "error": None,
    "seq_id": 1,
    "version": 1,
    "metadata": {...}
}
```

### After
```python
{
    "session_id": "uuid",
    "phone": "9876543210",
    "operation_type": "CREATE",
    "status": "LOADED",
    "created_at": "2024-11-17T...",
    "validation_errors": [],
    "process_result": None,
    "error": None,
    "seq_id": 1,
    "version": 1,
    "metadata": {...}
}
```

## Updated Flow

### Salon API (route_salon_request)

**Before:**
```
1. Prepare operation_data from payload
2. Call load_session(phone, data, task, operation_type)
3. Session contains data
4. Pass session to handler
```

**After:**
```
1. Call load_session(phone, task, operation_type)
2. Session contains seq_id and version only
3. Pass session and payload to handler
4. Handler uses payload for request data
```

### Handler Usage

**Before:**
```python
async def create_customer(payload, background_tasks, business_context, entity_context, session):
    # Get data from session
    operation_data = session["data"]
    phone = operation_data["phone"]
    name = operation_data["name"]
```

**After:**
```python
async def create_customer(payload, background_tasks, business_context, entity_context, session):
    # Get data from payload (already available)
    phone = payload.phone
    name = payload.name
    
    # Use session for seq_id and version
    seq_id = session["seq_id"]
    version = session["version"]
```

## Benefits

1. **Cleaner Separation** - Session handles metadata, payload handles data
2. **Reduced Coupling** - SessionManager doesn't need to know about request data
3. **Better Testability** - Easier to test session creation independently
4. **Simpler API** - Fewer parameters to pass around
5. **Flexibility** - Handlers have direct access to payload

## Method Responsibilities

### SessionManager.load_session()
- Create session object
- Get cache with read lock
- Check if phone exists
- Create new entry if needed (write lock)
- Add session mapping (write lock)
- Generate seq_id and version
- Return session with metadata

### Handler Functions
- Receive payload with request data
- Receive session with seq_id and version
- Use payload for business logic
- Use session for tracking

## Code Comparison

### Old Approach
```python
# In salon API
operation_data = {
    "phone": payload.phone,
    "name": payload.name or "",
    ...
}
session = entity_session_manager.load_session(
    phone=payload.phone,
    data=operation_data,
    task=payload.action,
    operation_type=operation_type
)

# In handler
phone = session["data"]["phone"]
name = session["data"]["name"]
```

### New Approach
```python
# In salon API
session = entity_session_manager.load_session(
    phone=payload.phone,
    task=payload.action,
    operation_type=operation_type
)

# In handler
phone = payload.phone
name = payload.name
seq_id = session["seq_id"]
version = session["version"]
```

## Performance Impact

- **Reduced Memory** - No duplicate data storage in session
- **Faster Execution** - No data copying/preparation
- **Cleaner Logs** - Session logs focus on metadata

## Backward Compatibility

- **Breaking Change** - Callers must update to new signature
- **Migration Path** - Update all load_session calls
- **Handler Updates** - Use payload instead of session["data"]

## Files Updated

1. **src/core/session.py**
   - Removed `data` parameter from `load_session()`
   - Removed `session["data"] = data` assignment

2. **src/business/salon/api.py**
   - Removed `operation_data` preparation
   - Updated `load_session()` call to remove `data` parameter

## Testing Considerations

### Before
```python
# Test with data in session
session = session_manager.load_session(
    phone="9876543210",
    data={"name": "John"},
    task="CREATE-CUSTOMER",
    operation_type=OperationType.CREATE
)
assert session["data"]["name"] == "John"
```

### After
```python
# Test without data in session
session = session_manager.load_session(
    phone="9876543210",
    task="CREATE-CUSTOMER",
    operation_type=OperationType.CREATE
)
assert session["seq_id"] == 1
assert session["version"] == 1
assert "data" not in session
```

## Future Enhancements

1. **Metadata Enrichment** - Add computed fields to session
2. **Session Validation** - Validate session state
3. **Session Expiry** - Auto-cleanup old sessions
4. **Session Hooks** - Pre/post session creation hooks
5. **Session Serialization** - Serialize session for storage

## Summary

The removal of the `data` parameter simplifies the `load_session()` method and improves separation of concerns. Request data is now handled directly by handlers via the payload, while the session focuses on metadata management (seq_id, version, tracking).

This change makes the code cleaner, more maintainable, and easier to understand.
