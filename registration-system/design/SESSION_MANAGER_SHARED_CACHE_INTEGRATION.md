# SessionManager Shared Cache Integration

## Overview

Updated `SessionManager` to use `SharedCustomerCache` and `SharedClientCache` for seq_id generation instead of the generic `MetadataManager`. This ensures proper entity-specific versioning and session tracking.

## Changes Made

### 1. SessionManager Constructor Update

**Before:**
```python
def __init__(self, universal_cache: UniversalCache):
    self.sessions = {}
    self.cache = universal_cache
    self.metadata_manager = MetadataManager(universal_cache)
```

**After:**
```python
def __init__(self, universal_cache: UniversalCache, entity_type: Optional[str] = None):
    self.sessions = {}
    self.cache = universal_cache
    self.metadata_manager = MetadataManager(universal_cache)
    self.entity_type = entity_type  # "customer" or "client"
```

### 2. load_session Method Update

**Key Changes:**
- Accepts `entity_type` parameter ("customer" or "client")
- Uses `SharedCustomerCache.generate_seq_id_for_create()` for customers
- Uses `SharedClientCache.generate_seq_id_for_create()` for clients
- Automatically adds session mapping to appropriate shared cache
- Falls back to MetadataManager if entity_type not specified

**Flow:**
```python
def load_session(self, phone, data, task, operation_type):
    # Create session first
    session = self.create_session(phone, operation_type)
    
    # Generate seq_id using shared cache based on entity_type
    if self.entity_type == "customer":
        seq_id = SharedCustomerCache.generate_seq_id_for_create(phone)
        SharedCustomerCache.add_customer_session(seq_id, phone, version, session_id)
    
    elif self.entity_type == "client":
        seq_id = SharedClientCache.generate_seq_id_for_create(phone)
        SharedClientCache.add_client_session(seq_id, phone, version, session_id)
    
    # Update session with seq_id and version
    session["seq_id"] = seq_id
    session["version"] = version
    
    return session
```

### 3. Salon API route_salon_request Update

**Key Changes:**
- Determines entity_type from action ("customer" or "client")
- Selects appropriate cache (customer_cache or client_cache)
- Creates first SessionManager without entity_type (for business-level session)
- Creates second SessionManager with entity_type (for entity-specific seq_id)

**Flow:**
```python
async def route_salon_request(payload, background_tasks, business_context, entity_context):
    # Determine entity_type from action
    if "customer" in action:
        entity_type = "customer"
        cache = entity_context.customer_cache
    else:
        entity_type = "client"
        cache = entity_context.client_cache
    
    # Create business-level session (no entity_type)
    session_manager = SessionManager(business_context.business_cache, entity_type=None)
    session = session_manager.create_session(phone, operation_type)
    
    # Create entity-level session with seq_id (with entity_type)
    entity_session_manager = SessionManager(cache, entity_type=entity_type)
    session = entity_session_manager.load_session(phone, data, task, operation_type)
    
    # Route to handler with session
    response = await handler(payload, background_tasks, business_context, entity_context, session)
```

## Shared Cache Integration

### SharedCustomerCache Methods Used

```python
# Generate seq_id for customer
seq_id = SharedCustomerCache.generate_seq_id_for_create(phone)

# Add session mapping
SharedCustomerCache.add_customer_session(seq_id, phone, version, session_id)

# Retrieve sessions
sessions = SharedCustomerCache.get_customer_sessions(seq_id, phone)
```

### SharedClientCache Methods Used

```python
# Generate seq_id for client
seq_id = SharedClientCache.generate_seq_id_for_create(phone)

# Add session mapping
SharedClientCache.add_client_session(seq_id, phone, version, session_id)

# Retrieve sessions
sessions = SharedClientCache.get_client_sessions(seq_id, phone)
```

## Thread Safety

### Shared Cache Thread Safety
- Each shared cache uses its own `_meta_lock` (threading.Lock)
- `generate_seq_id_for_create()` acquires lock for atomic increment
- `add_customer_session()` / `add_client_session()` acquire lock for atomic update
- File I/O protected by lock

### SessionManager Thread Safety
- `create_session()` uses UniversalCache read lock
- `load_session()` uses shared cache locks (not UniversalCache)
- No lock conflicts between SessionManager and shared caches

## Session Object Structure

Session returned from `load_session()`:
```python
{
    "session_id": "uuid",                    # Unique identifier
    "phone": "9876543210",                   # Customer/client phone
    "operation_type": "CREATE|UPDATE|DELETE", # Operation type
    "status": "LOADED",                      # Pipeline status
    "created_at": "2024-11-17T...",         # Creation timestamp
    "data": {...},                           # Operation data
    "validation_errors": [],                 # Validation errors
    "process_result": None,                  # Processing result
    "error": None,                           # Error message
    "seq_id": 1,                            # Sequential ID (from shared cache)
    "version": 1,                            # Version number
    "metadata": {...}                        # Metadata snapshot
}
```

## Metadata Structure

### Customer Metadata (SharedCustomerCache)
```json
{
    "metadata": {
        "total_customers": 5,
        "last_updated": "2024-11-17T..."
    },
    "1#9876543210": {
        "1": "session-uuid-1",
        "2": "session-uuid-2"
    },
    "2#9876543211": {
        "1": "session-uuid-3"
    }
}
```

### Client Metadata (SharedClientCache)
```json
{
    "metadata": {
        "total_clients": 3,
        "last_updated": "2024-11-17T..."
    },
    "1#9876543210": {
        "1": "session-uuid-1"
    },
    "2#9876543211": {
        "1": "session-uuid-2"
    }
}
```

## Seq_ID Generation

### Customer Seq_ID Generation
```
1. Acquire _meta_lock
2. Load SharedCustomerCache
3. Increment metadata.total_customers
4. seq_id = metadata.total_customers
5. Create entry: "{seq_id}#{phone}" = {}
6. Save to file
7. Release _meta_lock
8. Return seq_id
```

### Client Seq_ID Generation
```
1. Acquire _meta_lock
2. Load SharedClientCache
3. Increment metadata.total_clients
4. seq_id = metadata.total_clients
5. Create entry: "{seq_id}#{phone}" = {}
6. Save to file
7. Release _meta_lock
8. Return seq_id
```

## Session Mapping

### Customer Session Mapping
```
1. Acquire _meta_lock
2. Load SharedCustomerCache
3. Get or create entry: "{seq_id}#{phone}"
4. Add mapping: "{version}" → session_id
5. Save to file
6. Release _meta_lock
```

### Client Session Mapping
```
1. Acquire _meta_lock
2. Load SharedClientCache
3. Get or create entry: "{seq_id}#{phone}"
4. Add mapping: "{version}" → session_id
5. Save to file
6. Release _meta_lock
```

## Error Handling

### Fallback Mechanism
If `entity_type` is not specified:
```python
else:
    # Fallback to metadata manager if entity_type not specified
    self.cache.acquire_write_lock()
    try:
        seq_data = self.metadata_manager.generate_seq_id(phone, operation_type.value)
        seq_id = seq_data["seq_id"]
        version = seq_data["version"]
        
        self.metadata_manager.update_metadata(
            phone=phone,
            seq_id=seq_id,
            session_id=session["session_id"],
            version=version
        )
    finally:
        self.cache.release_write_lock()
```

### Exception Handling
```python
except Exception as e:
    logger.error(f"Failed to load session: {str(e)}", exc_info=True)
    raise
```

## Performance Characteristics

| Operation | Lock Type | Time | Concurrency |
|-----------|-----------|------|-------------|
| create_session | Read (UniversalCache) | O(1) | Multiple |
| generate_seq_id | Lock (Shared Cache) | O(1) | Single |
| add_session_mapping | Lock (Shared Cache) | O(1) | Single |
| load_session | Multiple locks | O(1) | Sequential |

## Integration Points

### Salon API
- Determines entity_type from action
- Creates two SessionManagers (business-level and entity-level)
- Passes session to handlers

### SessionManager
- Accepts entity_type parameter
- Routes to appropriate shared cache
- Maintains backward compatibility with fallback

### Shared Caches
- Generate seq_ids atomically
- Store session mappings
- Persist to files

## Benefits

1. **Entity-Specific Versioning** - Customers and clients have separate seq_id sequences
2. **Atomic Operations** - Seq_id generation and session mapping are atomic
3. **Audit Trail** - All sessions tracked with version history
4. **Thread-Safe** - Proper locking at each level
5. **Backward Compatible** - Fallback to MetadataManager if needed
6. **Scalable** - Separate caches for different entity types

## Migration Path

### Old Code
```python
session_manager = SessionManager(cache)
session = session_manager.load_session(phone, data, task, operation_type)
```

### New Code
```python
session_manager = SessionManager(cache, entity_type="customer")  # or "client"
session = session_manager.load_session(phone, data, task, operation_type)
```

### Backward Compatible
```python
session_manager = SessionManager(cache)  # entity_type=None
session = session_manager.load_session(phone, data, task, operation_type)
# Falls back to MetadataManager
```
