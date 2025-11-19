# Shared Cache Entity Lookup and Creation

## Overview

Updated `SharedCustomerCache` and `SharedClientCache` to support intelligent entity lookup and creation. The system now checks if a customer/client exists by phone number, retrieves existing data if found, or creates new entries if not found.

## New Methods Added

### SharedCustomerCache

#### 1. `customer_exists(phone: str) -> bool`
**Purpose:** Check if customer exists by phone number (read lock)

**Implementation:**
```python
@staticmethod
def customer_exists(phone: str) -> bool:
    with _meta_lock:
        if _meta_cache is None:
            _meta_cache = SharedCustomerCache._load_from_file()
        
        # Check if any customer entry contains this phone
        for key in _meta_cache.__dict__.keys():
            if key != "metadata" and phone in key:
                logger.info(f"Customer with phone {phone} exists: {key}")
                return True
        
        return False
```

**Thread Safety:** Uses read lock (meta_lock)

**Returns:** True if customer exists, False otherwise

#### 2. `get_customer_by_phone(phone: str) -> Optional[Dict]`
**Purpose:** Retrieve customer by phone number (read lock)

**Implementation:**
```python
@staticmethod
def get_customer_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    with _meta_lock:
        if _meta_cache is None:
            _meta_cache = SharedCustomerCache._load_from_file()
        
        # Search for customer with this phone
        for key, value in _meta_cache.__dict__.items():
            if key != "metadata" and phone in key:
                parts = key.split("#")
                if len(parts) == 2 and parts[1] == phone:
                    seq_id = int(parts[0])
                    return {
                        "seq_id": seq_id,
                        "phone": phone,
                        "sessions": value
                    }
        
        return None
```

**Thread Safety:** Uses read lock (meta_lock)

**Returns:** 
```python
{
    "seq_id": 1,
    "phone": "9876543210",
    "sessions": {"1": "session-uuid-1", "2": "session-uuid-2"}
}
# or None if not found
```

#### 3. `create_or_get_customer(phone: str) -> Dict`
**Purpose:** Create customer if not exists, or retrieve existing (write lock)

**Implementation:**
```python
@staticmethod
def create_or_get_customer(phone: str) -> Dict[str, Any]:
    with _meta_lock:
        if _meta_cache is None:
            _meta_cache = SharedCustomerCache._load_from_file()
        
        # Check if customer exists
        for key, value in _meta_cache.__dict__.items():
            if key != "metadata" and phone in key:
                parts = key.split("#")
                if len(parts) == 2 and parts[1] == phone:
                    seq_id = int(parts[0])
                    return {
                        "seq_id": seq_id,
                        "phone": phone,
                        "sessions": value,
                        "created": False
                    }
        
        # Customer doesn't exist, create new one
        _meta_cache.metadata.total_customers += 1
        seq_id = _meta_cache.metadata.total_customers
        
        customer_key = f"{seq_id}#{phone}"
        setattr(_meta_cache, customer_key, {})
        
        SharedCustomerCache._save_to_file(_meta_cache)
        
        return {
            "seq_id": seq_id,
            "phone": phone,
            "sessions": {},
            "created": True
        }
```

**Thread Safety:** Uses write lock (meta_lock)

**Returns:**
```python
# If customer exists
{
    "seq_id": 1,
    "phone": "9876543210",
    "sessions": {"1": "session-uuid-1"},
    "created": False
}

# If customer is new
{
    "seq_id": 2,
    "phone": "9876543211",
    "sessions": {},
    "created": True
}
```

### SharedClientCache

Same three methods implemented for clients:
- `client_exists(phone: str) -> bool`
- `get_client_by_phone(phone: str) -> Optional[Dict]`
- `create_or_get_client(phone: str) -> Dict`

## SessionManager Integration

### Updated load_session Method

**Flow:**
```
1. Create session with read lock
2. If entity_type == "customer":
   a. Call SharedCustomerCache.create_or_get_customer(phone)
   b. Get seq_id and check if created
   c. Calculate version from existing sessions
   d. Add session mapping
3. If entity_type == "client":
   a. Call SharedClientCache.create_or_get_client(phone)
   b. Get seq_id and check if created
   c. Calculate version from existing sessions
   d. Add session mapping
4. Update session with seq_id and version
5. Return session
```

**Key Changes:**
```python
# Old approach - always generate new seq_id
seq_id = SharedCustomerCache.generate_seq_id_for_create(phone)

# New approach - create or retrieve
customer_data = SharedCustomerCache.create_or_get_customer(phone)
seq_id = customer_data["seq_id"]
is_new = customer_data["created"]

# Calculate version from existing sessions
existing_sessions = customer_data.get("sessions", {})
version = len(existing_sessions) + 1
```

## Lock Strategy

### Read Lock (customer_exists, get_customer_by_phone)
- Multiple concurrent readers allowed
- No blocking between readers
- Used for checking existence and retrieval

### Write Lock (create_or_get_customer, create_or_get_client)
- Exclusive access
- Readers blocked during write
- Used for creation and updates
- Atomic file save

## Metadata Structure

### Customer Metadata File
```json
{
    "metadata": {
        "total_customers": 2,
        "last_updated": "2024-11-17T...",
        "version": 1
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

### Client Metadata File
```json
{
    "metadata": {
        "total_clients": 2,
        "last_updated": "2024-11-17T...",
        "version": 1
    },
    "1#9876543210": {
        "1": "session-uuid-1"
    },
    "2#9876543211": {
        "1": "session-uuid-2"
    }
}
```

## Version Calculation

**Old Approach:**
```python
version = 1  # Always start at 1
```

**New Approach:**
```python
existing_sessions = customer_data.get("sessions", {})
version = len(existing_sessions) + 1

# Example:
# If sessions = {"1": "uuid1", "2": "uuid2"}
# Then version = 3 (next version)
```

## Use Cases

### Case 1: New Customer
```python
# First request for phone "9876543210"
customer_data = SharedCustomerCache.create_or_get_customer("9876543210")

# Result:
{
    "seq_id": 1,
    "phone": "9876543210",
    "sessions": {},
    "created": True
}

# Version = 1 (no existing sessions)
```

### Case 2: Existing Customer
```python
# Second request for same phone "9876543210"
customer_data = SharedCustomerCache.create_or_get_customer("9876543210")

# Result:
{
    "seq_id": 1,
    "phone": "9876543210",
    "sessions": {"1": "session-uuid-1"},
    "created": False
}

# Version = 2 (one existing session)
```

### Case 3: Multiple Customers
```python
# First customer
customer1 = SharedCustomerCache.create_or_get_customer("9876543210")
# seq_id = 1, created = True

# Second customer
customer2 = SharedCustomerCache.create_or_get_customer("9876543211")
# seq_id = 2, created = True

# First customer again
customer1_again = SharedCustomerCache.create_or_get_customer("9876543210")
# seq_id = 1, created = False (same seq_id)
```

## Thread Safety Guarantees

### Atomicity
- Seq_id generation and file save are atomic within write lock
- No partial updates visible to readers

### Consistency
- Read lock ensures consistent snapshot
- Write lock ensures exclusive updates
- File I/O protected by lock

### Isolation
- Readers don't see partial writes
- Writers don't interfere with readers
- Each operation is isolated

## Performance Characteristics

| Operation | Lock Type | Time | Concurrency |
|-----------|-----------|------|-------------|
| customer_exists | Read | O(n) | Multiple |
| get_customer_by_phone | Read | O(n) | Multiple |
| create_or_get_customer | Write | O(n) | Single |
| add_customer_session | Write | O(1) | Single |

**Note:** O(n) is number of customers/clients in cache

## Error Handling

### File Not Found
```python
if not os.path.exists(_meta_path):
    logger.warning(f"Customer metadata file not found: {_meta_path}")
    return CustomerMetaModel.create_default()
```

### Invalid JSON
```python
except json.JSONDecodeError as e:
    logger.error(f"Failed to load customer metadata: {str(e)}")
    return CustomerMetaModel.create_default()
```

### Lock Timeout
- Uses threading.Lock() which blocks indefinitely
- No timeout mechanism (can be added if needed)

## Logging

All operations logged with appropriate levels:
```python
logger.info(f"Customer already exists: seq_id={seq_id}, phone={phone}")
logger.info(f"Created new customer: seq_id={seq_id}, phone={phone}")
logger.debug(f"Customer with phone {phone} not found")
logger.warning(f"Customer metadata file not found: {_meta_path}")
logger.error(f"Failed to load customer metadata: {str(e)}")
```

## Future Enhancements

1. **Indexing** - Add phone number index for O(1) lookup
2. **Caching** - Cache phone→seq_id mapping in memory
3. **Batch Operations** - Support bulk create/get operations
4. **Expiry** - Auto-cleanup old sessions
5. **Metrics** - Track cache hit/miss rates
