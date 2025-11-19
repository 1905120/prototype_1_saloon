# Salon API Updates

## Overview

Updated `src/business/salon/api.py` to integrate SessionManager and context-based caching for proper session and seq_id management.

## Key Changes

### 1. Session Creation in route_salon_request

**Before:** Handlers directly called manager methods without session tracking

**After:** 
```python
# Create session manager with business context cache
session_manager = SessionManager(business_context.business_cache)

# Create session with read lock
session = session_manager.create_session(
    phone=payload.phone,
    operation_type=operation_type
)

# Load session with seq_id generation using entity context cache
entity_session_manager = SessionManager(cache)
session = entity_session_manager.load_session(
    phone=payload.phone,
    data=operation_data,
    task=payload.action,
    operation_type=operation_type
)
```

### 2. Session Flow

```
route_salon_request()
  ↓
1. Determine operation_type from action
2. Create SessionManager with business_context.business_cache
3. Create session (read lock) → session_id generated
4. Create SessionManager with entity_context cache
5. Load session (write lock) → seq_id and version generated
6. Store session_id, seq_id, version in payload
7. Pass session to handler
  ↓
Handler (create_customer, update_customer, etc.)
  ↓
1. Receive session with seq_id and version
2. Execute business logic
3. Log operation with session details
4. Return SessionResponse with session_id
```

### 3. Utility Functions Added

#### `queue_operation(operation_type, data, business_context, entity_context)`
- Queues operation for background processing
- Returns session_id for tracking
- Uses WorkerManager singleton

#### `get_operation_result(session_id, timeout)`
- Retrieves result of queued operation
- Optional timeout parameter
- Returns None if not ready

#### `validate_phone(phone)`
- Validates phone number format
- Checks for 10-15 digits
- Removes common formatting characters

#### `validate_customer_data(data)`
- Validates customer creation data
- Checks phone, name requirements
- Returns (is_valid, error_message) tuple

#### `validate_client_data(data)`
- Validates client (salon) creation data
- Checks phone, owner_name, salon_name, service_type
- Returns (is_valid, error_message) tuple

#### `log_operation(action, phone, status, session_id, details)`
- Logs operation details for audit trail
- Includes timestamp and session tracking
- Supports additional details dictionary

### 4. Handler Updates

All handlers now:
- Accept `session` parameter from route_salon_request
- Use session_id from session object
- Include seq_id and version in logs
- Call log_operation for audit trail
- Pass session details to SessionResponse

**Example:**
```python
async def create_customer(payload, background_tasks, business_context, entity_context, session):
    # ... validation ...
    
    customer_record = entity_context.customer_manager.create_customer(...)
    
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
```

### 5. Session Object Structure

Session passed to handlers contains:
```python
{
    "session_id": "uuid",                    # Unique identifier
    "phone": "9876543210",                   # Customer/client phone
    "operation_type": "CREATE|UPDATE|DELETE", # Operation type
    "status": "LOADED|CACHED|VALIDATED|...", # Pipeline status
    "created_at": "2024-11-17T...",         # Creation timestamp
    "data": {...},                           # Operation data
    "seq_id": 1,                            # Sequential ID
    "version": 1,                            # Version number
    "metadata": {...},                       # Metadata snapshot
    "max_customers": 100                     # Max customers limit
}
```

## Thread Safety

### Read Lock (create_session)
- Multiple concurrent readers allowed
- Metadata snapshot captured at creation
- No blocking between readers

### Write Lock (load_session)
- Exclusive access for seq_id generation
- Readers blocked during write
- Atomic metadata update

## Integration Points

### BusinessContext
- Provides `business_cache` (UniversalCache)
- Used for business-level session creation
- Manages phone mappings

### CustomerContext / ClientContext
- Provides `customer_cache` or `client_cache` (UniversalCache)
- Used for entity-level seq_id generation
- Manages entity-specific metadata

### SessionManager
- Creates sessions with read lock
- Loads sessions with write lock
- Generates seq_id and version
- Updates metadata atomically

## Error Handling

All handlers include:
- Validation error handling (400 status)
- Processing error handling (500 status)
- Detailed error logging with exc_info=True
- Graceful exception propagation

## Audit Trail

Each operation logged with:
- Action type (CREATE-CUSTOMER, UPDATE-CLIENT, etc.)
- Phone number
- Status (COMPLETED, FAILED)
- Session ID
- Seq ID and version
- Entity ID (customerId, clientId)
- Timestamp
- Additional operation-specific details

## Performance Characteristics

| Operation | Lock Type | Time | Notes |
|-----------|-----------|------|-------|
| create_session | Read | O(1) | Multiple concurrent |
| load_session | Write | O(1) | Single exclusive |
| Handler execution | None | O(n) | Depends on business logic |
| log_operation | None | O(1) | In-memory logging |

## Future Enhancements

1. **Async Session Loading** - Use async/await for I/O operations
2. **Session Caching** - Cache sessions in memory for quick retrieval
3. **Batch Operations** - Support multiple operations in single request
4. **Session Expiry** - Auto-cleanup old sessions
5. **Metrics Collection** - Track operation latencies and success rates
