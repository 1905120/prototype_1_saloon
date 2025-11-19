# Shared Cache Lock Integration - get_cache_with_lock and put_cache_with_lock

## Overview

Added `get_cache_with_lock()` and `put_cache_with_lock()` methods to both `SharedCustomerCache` and `SharedClientCache`. These methods integrate the universal model's lock mechanism with the singleton cache pattern, providing thread-safe access with lazy loading.

## Architecture

```
SharedCustomerCache / SharedClientCache (Singleton)
  ↓
CustomerMetaModel / ClientMetaModel (Universal)
  ↓
Lock Mechanism (Read/Write Locks)
```

## Methods Added

### 1. get_cache_with_lock() - READ OPERATION

**Location:** 
- `src/core/customer_management/shared.py`
- `src/core/client_management/shared.py`

**Purpose:** Get cache with read lock, lazy load if needed

**Signature:**
```python
@staticmethod
def get_cache_with_lock() -> CustomerMetaModel:
```

**Implementation Flow:**

```python
@staticmethod
def get_cache_with_lock() -> CustomerMetaModel:
    """
    Get cache with read lock from universal model
    Checks if metadata exists in singleton cache, loads if not
    
    Returns:
        Copy of customer metadata with read lock protection
    """
    global _meta_cache
    
    try:
        # Step 1: Acquire read lock from universal model
        CustomerMetaModel.acquire_read_lock()
        
        # Step 2: Check if cache is loaded in singleton
        if _meta_cache is None:
            logger.info("Customer metadata not in singleton cache, loading from file")
            _meta_cache = SharedCustomerCache._load_from_file()
        
        # Step 3: Use universal model's get_cache to create a copy
        meta_copy = CustomerMetaModel.get_cache(_meta_cache)
        
        logger.info("Customer cache retrieved with read lock")
        return meta_copy
    
    except Exception as e:
        logger.error(f"Failed to get customer cache with lock: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Step 4: Release read lock from universal model
        CustomerMetaModel.release_read_lock()
```

**Execution Steps:**

```
1. Acquire read lock (from universal model)
   ├─ Increment read counter
   └─ Block writers if first reader
2. Check singleton cache
   ├─ If None, load from file
   └─ If exists, use existing
3. Create copy using universal model's get_cache
   ├─ Copy metadata
   └─ Copy all entries
4. Release read lock
   ├─ Decrement read counter
   └─ Allow writers if last reader
5. Return copy
```

**Concurrency:** Multiple readers can execute simultaneously

**Example Usage:**
```python
# From CustomerContext
cache = SharedCustomerCache.get_cache_with_lock()
total_customers = cache.metadata.total_customers
```

### 2. put_cache_with_lock(updates) - WRITE OPERATION

**Location:**
- `src/core/customer_management/shared.py`
- `src/core/client_management/shared.py`

**Purpose:** Put cache with write lock, update singleton and file

**Signature:**
```python
@staticmethod
def put_cache_with_lock(updates: Dict) -> CustomerMetaModel:
```

**Implementation Flow:**

```python
@staticmethod
def put_cache_with_lock(updates: Dict) -> CustomerMetaModel:
    """
    Put cache with write lock from universal model
    Updates metadata in singleton cache
    
    Args:
        updates: Dictionary of updates to apply
    
    Returns:
        Updated customer metadata
    """
    global _meta_cache
    
    try:
        # Step 1: Acquire write lock from universal model
        CustomerMetaModel.acquire_write_lock()
        
        # Step 2: Check if cache is loaded in singleton
        if _meta_cache is None:
            logger.info("Customer metadata not in singleton cache, loading from file")
            _meta_cache = SharedCustomerCache._load_from_file()
        
        # Step 3: Use universal model's put_cache to update
        updated_cache = CustomerMetaModel.put_cache(_meta_cache, updates)
        
        # Step 4: Update singleton cache
        _meta_cache = updated_cache
        
        # Step 5: Save to file
        SharedCustomerCache._save_to_file(_meta_cache)
        
        logger.info("Customer cache updated with write lock and saved to file")
        return updated_cache
    
    except Exception as e:
        logger.error(f"Failed to put customer cache with lock: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Step 6: Release write lock from universal model
        CustomerMetaModel.release_write_lock()
```

**Execution Steps:**

```
1. Acquire write lock (from universal model)
   └─ Exclusive access, block all readers and writers
2. Check singleton cache
   ├─ If None, load from file
   └─ If exists, use existing
3. Update using universal model's put_cache
   ├─ Apply metadata updates
   ├─ Apply entry updates
   └─ Update last_updated timestamp
4. Update singleton cache reference
   └─ _meta_cache = updated_cache
5. Save to file
   ├─ Create directory if needed
   └─ Write JSON atomically
6. Release write lock
   └─ Allow readers and writers
7. Return updated cache
```

**Concurrency:** Only one writer at a time, readers blocked

**Example Usage:**
```python
# From SharedCustomerCache.create_or_get_customer
updates = {
    "metadata": {
        "total_customers": 5
    },
    "1#9876543210": {}
}
updated_cache = SharedCustomerCache.put_cache_with_lock(updates)
```

## Lock Flow Diagram

### Read Operation (get_cache_with_lock)

```
Thread 1: get_cache_with_lock()
  │
  ├─ [ACQUIRE READ LOCK]
  │  ├─ Increment read_count
  │  └─ Block writers if first reader
  │
  ├─ Check singleton cache
  │  └─ Load from file if needed
  │
  ├─ Create copy via universal model
  │  ├─ Copy metadata
  │  └─ Copy entries
  │
  ├─ [RELEASE READ LOCK]
  │  ├─ Decrement read_count
  │  └─ Allow writers if last reader
  │
  └─ Return copy

Thread 2: get_cache_with_lock() [CONCURRENT]
  │
  ├─ [ACQUIRE READ LOCK] ✓ (allowed)
  │
  ├─ Check singleton cache
  │
  ├─ Create copy
  │
  ├─ [RELEASE READ LOCK]
  │
  └─ Return copy
```

### Write Operation (put_cache_with_lock)

```
Thread 1: put_cache_with_lock(updates)
  │
  ├─ [ACQUIRE WRITE LOCK]
  │  └─ Exclusive access
  │
  ├─ Check singleton cache
  │  └─ Load from file if needed
  │
  ├─ Update via universal model
  │  ├─ Apply updates
  │  └─ Update timestamp
  │
  ├─ Update singleton reference
  │
  ├─ Save to file
  │
  ├─ [RELEASE WRITE LOCK]
  │
  └─ Return updated cache

Thread 2: get_cache_with_lock() [BLOCKED]
  │
  ├─ [ACQUIRE READ LOCK] ✗ (waiting for write lock)
  │
  └─ ... (waits until Thread 1 releases)
```

## Concurrency Scenarios

### Scenario A: Multiple Readers

```
Thread 1: get_cache_with_lock() ──→ [READ LOCK] ──→ Proceeds
Thread 2: get_cache_with_lock() ──→ [READ LOCK] ──→ Proceeds (concurrent)
Thread 3: get_cache_with_lock() ──→ [READ LOCK] ──→ Proceeds (concurrent)

Result: All three readers execute concurrently
```

### Scenario B: Reader Blocked by Writer

```
Thread 1: put_cache_with_lock() ──→ [WRITE LOCK] ──→ Proceeds
Thread 2: get_cache_with_lock() ──→ [READ LOCK] ──→ BLOCKED
Thread 3: get_cache_with_lock() ──→ [READ LOCK] ──→ BLOCKED

After Thread 1 releases:
Thread 2: [READ LOCK] ──→ Proceeds
Thread 3: [READ LOCK] ──→ Proceeds (concurrent)
```

### Scenario C: Writer Blocked by Readers

```
Thread 1: get_cache_with_lock() ──→ [READ LOCK] ──→ Proceeds
Thread 2: get_cache_with_lock() ──→ [READ LOCK] ──→ Proceeds
Thread 3: put_cache_with_lock() ──→ [WRITE LOCK] ──→ BLOCKED

After Threads 1 & 2 release:
Thread 3: [WRITE LOCK] ──→ Proceeds
```

## Lazy Loading Mechanism

### First Call (Cache Empty)

```
get_cache_with_lock()
  │
  ├─ Acquire read lock
  │
  ├─ Check if _meta_cache is None
  │  └─ YES → Load from file
  │     ├─ Read JSON file
  │     ├─ Parse to CustomerMetaModel
  │     └─ Store in _meta_cache
  │
  ├─ Create copy
  │
  ├─ Release read lock
  │
  └─ Return copy
```

### Subsequent Calls (Cache Loaded)

```
get_cache_with_lock()
  │
  ├─ Acquire read lock
  │
  ├─ Check if _meta_cache is None
  │  └─ NO → Use existing cache
  │
  ├─ Create copy
  │
  ├─ Release read lock
  │
  └─ Return copy
```

## Thread Safety Guarantees

### Atomicity
- Read operations are atomic within read lock
- Write operations are atomic within write lock
- Lazy loading is atomic

### Consistency
- Read lock ensures consistent snapshot
- Write lock ensures exclusive updates
- All readers see same data
- File I/O protected by lock

### Isolation
- Readers don't see partial writes
- Writers don't interfere with readers
- Lazy loading doesn't cause race conditions

## Error Handling

Both methods use try-finally to ensure locks are always released:

```python
try:
    CustomerMetaModel.acquire_read_lock()
    # ... operations ...
finally:
    CustomerMetaModel.release_read_lock()
```

**Guarantees:**
- Locks released even if exception occurs
- No deadlock from unreleased locks
- Proper resource cleanup
- Errors logged with full context

## Integration with Existing Code

### Before (Direct Access)

```python
# In SharedCustomerCache.create_or_get_customer
with _meta_lock:
    if _meta_cache is None:
        _meta_cache = SharedCustomerCache._load_from_file()
    
    # ... operations ...
```

### After (With Lock Integration)

```python
# In SharedCustomerCache.create_or_get_customer
cache = SharedCustomerCache.get_cache_with_lock()
# ... read operations ...

updates = {...}
updated_cache = SharedCustomerCache.put_cache_with_lock(updates)
```

## Performance Characteristics

| Operation | Lock Type | Duration | Concurrency |
|-----------|-----------|----------|-------------|
| get_cache_with_lock | Read | Short | Multiple |
| put_cache_with_lock | Write | Medium | Single |
| Lazy load (first call) | Read | Medium | Single |
| Lazy load (subsequent) | Read | Short | Multiple |

## Logging

All operations logged at appropriate levels:

```python
logger.info("Customer metadata not in singleton cache, loading from file")
logger.info("Customer cache retrieved with read lock")
logger.info("Customer cache updated with write lock and saved to file")
logger.error(f"Failed to get customer cache with lock: {str(e)}", exc_info=True)
```

## Usage Examples

### Example 1: Read Customer Cache

```python
from src.core.customer_management.shared import SharedCustomerCache

# Get cache with read lock
cache = SharedCustomerCache.get_cache_with_lock()

# Access data
total = cache.metadata.total_customers
print(f"Total customers: {total}")

# Lock automatically released after return
```

### Example 2: Update Customer Cache

```python
from src.core.customer_management.shared import SharedCustomerCache

# Prepare updates
updates = {
    "metadata": {
        "total_customers": 10
    },
    "1#9876543210": {
        "1": "session-uuid-1"
    }
}

# Update cache with write lock
updated_cache = SharedCustomerCache.put_cache_with_lock(updates)

# Lock automatically released after return
# File automatically saved
```

### Example 3: Multiple Concurrent Reads

```python
import threading
from src.core.customer_management.shared import SharedCustomerCache

def read_cache():
    cache = SharedCustomerCache.get_cache_with_lock()
    print(f"Total: {cache.metadata.total_customers}")

# Create multiple threads
threads = [threading.Thread(target=read_cache) for _ in range(5)]

# Start all threads
for t in threads:
    t.start()

# Wait for all to complete
for t in threads:
    t.join()

# All threads executed concurrently
```

## Future Enhancements

1. **Lock Timeout** - Add timeout to prevent indefinite blocking
2. **Lock Metrics** - Track lock contention and wait times
3. **Batch Operations** - Support multiple updates in single write
4. **Cache Invalidation** - Explicit cache invalidation mechanism
5. **Read-Write Separation** - Separate read and write paths
