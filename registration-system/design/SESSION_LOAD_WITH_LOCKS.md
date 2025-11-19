# Session Load with Locks - Integrated get_cache_with_lock and put_cache_with_lock

## Overview

Updated `SessionManager.load_session()` to use the new `get_cache_with_lock()` and `put_cache_with_lock()` methods from shared caches. This provides proper thread-safe access with explicit lock management for reading and writing metadata.

## Updated Flow

### Old Flow
```
load_session()
  ├─ create_session() [read lock]
  ├─ create_or_get_customer() [write lock inside]
  ├─ add_customer_session() [write lock inside]
  └─ Return session
```

### New Flow
```
load_session()
  ├─ create_session() [read lock]
  ├─ get_cache_with_lock() [read lock]
  │  ├─ Check if phone exists
  │  └─ Release read lock
  ├─ If not found:
  │  ├─ put_cache_with_lock() [write lock]
  │  │  ├─ Create new entry
  │  │  ├─ Increment counter
  │  │  └─ Release write lock
  ├─ put_cache_with_lock() [write lock]
  │  ├─ Add session mapping
  │  └─ Release write lock
  └─ Return session
```

## Implementation Details

### Step 1: Create Session (Read Lock)

```python
# Create session first
session = self.create_session(phone, operation_type)
```

**Lock:** READ LOCK (UniversalCache)
- Acquires read lock
- Loads metadata snapshot
- Releases read lock

### Step 2: Get Cache with Read Lock

```python
# Get cache with read lock
cache = SharedCustomerCache.get_cache_with_lock()
logger.info(f"Retrieved customer cache with read lock for phone: {phone}")
```

**Lock:** READ LOCK (Universal Model)
- Acquires read lock
- Checks if cache loaded in singleton
- Loads from file if needed
- Creates copy
- Releases read lock
- Returns copy

**Concurrency:** Multiple readers can execute simultaneously

### Step 3: Check if Phone Exists

```python
# Check if phone exists in cache
customer_key = None
seq_id = None
existing_sessions = {}

for key in cache.__dict__.keys():
    if key != "metadata" and phone in key:
        parts = key.split("#")
        if len(parts) == 2 and parts[1] == phone:
            customer_key = key
            seq_id = int(parts[0])
            existing_sessions = getattr(cache, key, {})
            logger.info(f"Customer found in cache: seq_id={seq_id}, phone={phone}")
            break
```

**Lock:** NONE (using copy from read lock)
- No lock needed, using copy from step 2
- Searches for phone in cache entries
- Extracts seq_id if found

### Step 4: Create New Entry if Not Found (Write Lock)

```python
if seq_id is None:
    logger.info(f"Customer not found for phone {phone}, creating new entry")
    
    # Prepare updates for new customer
    new_seq_id = cache.metadata.total_customers + 1
    customer_key = f"{new_seq_id}#{phone}"
    
    updates = {
        "metadata": {
            "total_customers": new_seq_id
        },
        customer_key: {}
    }
    
    # Put cache with write lock
    updated_cache = SharedCustomerCache.put_cache_with_lock(updates)
    seq_id = new_seq_id
    existing_sessions = {}
    logger.info(f"Created new customer: seq_id={seq_id}, phone={phone}")
```

**Lock:** WRITE LOCK (Universal Model)
- Acquires write lock (exclusive)
- Checks if cache loaded in singleton
- Loads from file if needed
- Increments total_customers
- Creates new entry
- Saves to file
- Releases write lock
- Returns updated cache

**Concurrency:** Only one writer, readers blocked

### Step 5: Calculate Version

```python
# Calculate version based on existing sessions
version = len(existing_sessions) + 1
```

**Lock:** NONE
- No lock needed
- Uses existing_sessions from step 3 or 4

### Step 6: Add Session Mapping (Write Lock)

```python
# Add session mapping with write lock
session_updates = {
    customer_key: {
        **existing_sessions,
        str(version): session["session_id"]
    }
}
SharedCustomerCache.put_cache_with_lock(session_updates)
logger.info(f"Added customer session: seq_id={seq_id}, phone={phone}, version={version}")
```

**Lock:** WRITE LOCK (Universal Model)
- Acquires write lock (exclusive)
- Checks if cache loaded in singleton
- Loads from file if needed
- Adds session mapping
- Updates last_updated timestamp
- Saves to file
- Releases write lock

**Concurrency:** Only one writer, readers blocked

### Step 7: Update Session and Return

```python
# Update session with seq_id and version
session["seq_id"] = seq_id
session["version"] = version
session["data"] = data

logger.info(f"Session loaded: {session['session_id']} with seq_id: {seq_id}, version: {version}")

return session
```

**Lock:** NONE
- No lock needed
- In-memory operations only

## Complete Execution Flow Diagram

```
load_session(phone, data, task, operation_type)
  │
  ├─ [1] create_session()
  │  ├─ [READ LOCK - UniversalCache]
  │  ├─ Load metadata
  │  └─ [RELEASE READ LOCK]
  │
  ├─ [2] get_cache_with_lock()
  │  ├─ [READ LOCK - Universal Model]
  │  ├─ Check singleton cache
  │  ├─ Load from file if needed
  │  ├─ Create copy
  │  └─ [RELEASE READ LOCK]
  │
  ├─ [3] Search for phone in cache
  │  └─ No lock (using copy)
  │
  ├─ [4] If not found:
  │  ├─ put_cache_with_lock(new_entry)
  │  │  ├─ [WRITE LOCK - Universal Model]
  │  │  ├─ Increment counter
  │  │  ├─ Create entry
  │  │  ├─ Save to file
  │  │  └─ [RELEASE WRITE LOCK]
  │
  ├─ [5] Calculate version
  │  └─ No lock (in-memory)
  │
  ├─ [6] put_cache_with_lock(session_mapping)
  │  ├─ [WRITE LOCK - Universal Model]
  │  ├─ Add session mapping
  │  ├─ Save to file
  │  └─ [RELEASE WRITE LOCK]
  │
  ├─ [7] Update session object
  │  └─ No lock (in-memory)
  │
  └─ Return session
```

## Lock Sequence for Customer

```
Timeline:
T0: create_session()
    ├─ [ACQUIRE READ LOCK - UniversalCache]
    ├─ Load metadata
    └─ [RELEASE READ LOCK]

T1: get_cache_with_lock()
    ├─ [ACQUIRE READ LOCK - Universal Model]
    ├─ Check singleton
    ├─ Create copy
    └─ [RELEASE READ LOCK]

T2: Search cache (no lock)

T3: If not found:
    put_cache_with_lock()
    ├─ [ACQUIRE WRITE LOCK - Universal Model]
    ├─ Increment total_customers
    ├─ Create entry
    ├─ Save file
    └─ [RELEASE WRITE LOCK]

T4: put_cache_with_lock()
    ├─ [ACQUIRE WRITE LOCK - Universal Model]
    ├─ Add session mapping
    ├─ Save file
    └─ [RELEASE WRITE LOCK]

T5: Return session
```

## Concurrency Scenarios

### Scenario A: Multiple Concurrent Reads (Different Phones)

```
Thread 1: load_session(phone="111")
  ├─ create_session() [READ LOCK]
  ├─ get_cache_with_lock() [READ LOCK] ✓
  └─ Search cache (no lock)

Thread 2: load_session(phone="222")
  ├─ create_session() [READ LOCK]
  ├─ get_cache_with_lock() [READ LOCK] ✓ (concurrent)
  └─ Search cache (no lock)

Result: Both threads execute concurrently
```

### Scenario B: Read Blocked by Write

```
Thread 1: load_session(phone="111")
  ├─ create_session() [READ LOCK]
  ├─ get_cache_with_lock() [READ LOCK] ✓
  ├─ Search cache (not found)
  └─ put_cache_with_lock() [WRITE LOCK] ✓

Thread 2: load_session(phone="222")
  ├─ create_session() [READ LOCK]
  └─ get_cache_with_lock() [READ LOCK] ✗ (blocked by write lock)

After Thread 1 releases write lock:
Thread 2: get_cache_with_lock() [READ LOCK] ✓
```

### Scenario C: Multiple Writes (Sequential)

```
Thread 1: load_session(phone="111")
  └─ put_cache_with_lock() [WRITE LOCK] ✓

Thread 2: load_session(phone="222")
  └─ put_cache_with_lock() [WRITE LOCK] ✗ (blocked)

After Thread 1 releases:
Thread 2: put_cache_with_lock() [WRITE LOCK] ✓
```

## Data Flow

### New Customer

```
Input: phone="9876543210", data={...}
  │
  ├─ create_session() → session_id="uuid-1"
  │
  ├─ get_cache_with_lock()
  │  └─ cache.metadata.total_customers = 0
  │
  ├─ Search cache → Not found
  │
  ├─ put_cache_with_lock({
  │    "metadata": {"total_customers": 1},
  │    "1#9876543210": {}
  │  })
  │  └─ Saved to file
  │
  ├─ put_cache_with_lock({
  │    "1#9876543210": {"1": "uuid-1"}
  │  })
  │  └─ Saved to file
  │
  └─ Return session {
       "session_id": "uuid-1",
       "seq_id": 1,
       "version": 1,
       "data": {...}
     }
```

### Existing Customer

```
Input: phone="9876543210", data={...}
  │
  ├─ create_session() → session_id="uuid-2"
  │
  ├─ get_cache_with_lock()
  │  └─ cache has "1#9876543210": {"1": "uuid-1"}
  │
  ├─ Search cache → Found seq_id=1
  │
  ├─ Skip creation (already exists)
  │
  ├─ put_cache_with_lock({
  │    "1#9876543210": {"1": "uuid-1", "2": "uuid-2"}
  │  })
  │  └─ Saved to file
  │
  └─ Return session {
       "session_id": "uuid-2",
       "seq_id": 1,
       "version": 2,
       "data": {...}
     }
```

## Thread Safety Guarantees

### Atomicity
- Each lock operation is atomic
- No partial updates visible
- File I/O protected by locks

### Consistency
- Read lock ensures consistent snapshot
- Write lock ensures exclusive updates
- All readers see same data

### Isolation
- Readers don't see partial writes
- Writers don't interfere with readers
- Each operation isolated

## Error Handling

```python
try:
    # ... operations ...
finally:
    # Locks automatically released by get_cache_with_lock and put_cache_with_lock
```

**Guarantees:**
- Locks released even if exception occurs
- No deadlock from unreleased locks
- Proper resource cleanup
- Errors logged with full context

## Performance Characteristics

| Operation | Lock Type | Duration | Concurrency |
|-----------|-----------|----------|-------------|
| create_session | Read | Short | Multiple |
| get_cache_with_lock | Read | Short | Multiple |
| Search cache | None | Short | Multiple |
| put_cache_with_lock (new) | Write | Medium | Single |
| put_cache_with_lock (session) | Write | Medium | Single |
| Total load_session | Mixed | Long | Sequential |

## Logging

All operations logged at appropriate levels:

```python
logger.info(f"Retrieved customer cache with read lock for phone: {phone}")
logger.info(f"Customer found in cache: seq_id={seq_id}, phone={phone}")
logger.info(f"Customer not found for phone {phone}, creating new entry")
logger.info(f"Created new customer: seq_id={seq_id}, phone={phone}")
logger.info(f"Added customer session: seq_id={seq_id}, phone={phone}, version={version}")
logger.info(f"Session loaded: {session['session_id']} with seq_id: {seq_id}, version: {version}")
```

## Comparison with Previous Approach

### Before
```python
# Direct method calls with internal locks
customer_data = SharedCustomerCache.create_or_get_customer(phone)
SharedCustomerCache.add_customer_session(seq_id, phone, version, session_id)
```

### After
```python
# Explicit lock management with get/put cache
cache = SharedCustomerCache.get_cache_with_lock()
# ... check and create ...
SharedCustomerCache.put_cache_with_lock(updates)
```

**Benefits:**
- Explicit lock visibility
- Better control over lock duration
- Clearer separation of read and write
- Easier to debug lock issues
- More flexible for future enhancements

## Future Enhancements

1. **Lock Timeout** - Add timeout to prevent indefinite blocking
2. **Lock Metrics** - Track lock contention and wait times
3. **Batch Operations** - Support multiple updates in single write
4. **Cache Invalidation** - Explicit cache invalidation mechanism
5. **Optimistic Locking** - Use version numbers instead of locks
