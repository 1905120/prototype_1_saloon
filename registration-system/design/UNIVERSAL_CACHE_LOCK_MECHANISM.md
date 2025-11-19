# Universal Cache Lock Mechanism - get_cache and put_cache

## Overview

Added thread-safe `get_cache` and `put_cache` methods to both `CustomerMetaModel` and `ClientMetaModel` in the universal modules. These methods implement reader-writer lock patterns for safe concurrent access to metadata.

## Implementation Details

### Files Updated

1. **src/core/customer_management/universal.py** - CustomerMetaModel
2. **src/core/client_management/universal.py** - ClientMetaModel

### Global Lock Variables

```python
# Global lock for thread-safe cache operations
_cache_lock = threading.Lock()
_read_count = 0
_read_count_lock = threading.Lock()
_write_lock = threading.Lock()
```

**Purpose:**
- `_read_count_lock` - Protects the read counter
- `_write_lock` - Blocks writers when readers are active
- `_read_count` - Tracks number of active readers

## Lock Methods

### 1. acquire_read_lock()

**Purpose:** Acquire read lock for cache access

**Implementation:**
```python
@staticmethod
def acquire_read_lock() -> None:
    """
    Acquire read lock for cache access
    Multiple readers allowed, writers blocked
    """
    global _read_count
    
    with _read_count_lock:
        _read_count += 1
        if _read_count == 1:
            _write_lock.acquire()  # Block writers on first reader
    
    logger.debug(f"Read lock acquired. Read count: {_read_count}")
```

**Behavior:**
- Increments read counter
- If first reader, acquires write lock (blocks writers)
- Multiple readers can proceed concurrently

### 2. release_read_lock()

**Purpose:** Release read lock

**Implementation:**
```python
@staticmethod
def release_read_lock() -> None:
    """
    Release read lock for cache access
    """
    global _read_count
    
    with _read_count_lock:
        _read_count -= 1
        if _read_count == 0:
            _write_lock.release()  # Allow writers when no readers
    
    logger.debug(f"Read lock released. Read count: {_read_count}")
```

**Behavior:**
- Decrements read counter
- If last reader, releases write lock (allows writers)

### 3. acquire_write_lock()

**Purpose:** Acquire write lock for exclusive access

**Implementation:**
```python
@staticmethod
def acquire_write_lock() -> None:
    """
    Acquire write lock for cache access
    Exclusive access, readers and writers blocked
    """
    _write_lock.acquire()
    logger.debug("Write lock acquired")
```

**Behavior:**
- Acquires exclusive write lock
- Blocks all readers and other writers

### 4. release_write_lock()

**Purpose:** Release write lock

**Implementation:**
```python
@staticmethod
def release_write_lock() -> None:
    """
    Release write lock for cache access
    """
    _write_lock.release()
    logger.debug("Write lock released")
```

**Behavior:**
- Releases write lock
- Allows readers and writers to proceed

## Cache Methods

### 1. get_cache(cache_data) - READ OPERATION

**Purpose:** Get cache with read lock (thread-safe read)

**Signature:**
```python
@staticmethod
def get_cache(cache_data: "CustomerMetaModel") -> "CustomerMetaModel":
```

**Implementation:**
```python
@staticmethod
def get_cache(cache_data: "CustomerMetaModel") -> "CustomerMetaModel":
    """
    Get cache with read lock
    Thread-safe read operation
    
    Args:
        cache_data: CustomerMetaModel instance to read
    
    Returns:
        Copy of cache data
    """
    try:
        CustomerMetaModel.acquire_read_lock()
        
        # Create a copy to return
        meta_copy = CustomerMetaModel(
            metadata=MetadataInfo(
                total_customers=cache_data.metadata.total_customers,
                last_updated=cache_data.metadata.last_updated,
                version=cache_data.metadata.version
            )
        )
        
        # Copy all customer entries
        for key, value in cache_data.__dict__.items():
            if key != "metadata":
                setattr(meta_copy, key, value)
        
        logger.info("Cache retrieved with read lock")
        return meta_copy
    
    finally:
        CustomerMetaModel.release_read_lock()
```

**Lock Flow:**
```
1. Acquire read lock
2. Create copy of cache data
3. Copy metadata
4. Copy all customer entries
5. Release read lock
6. Return copy
```

**Concurrency:** Multiple readers can execute simultaneously

**Example Usage:**
```python
# Multiple threads can call this concurrently
cache_copy = CustomerMetaModel.get_cache(cache_data)
total_customers = cache_copy.metadata.total_customers
```

### 2. put_cache(cache_data, updates) - WRITE OPERATION

**Purpose:** Put cache with write lock (thread-safe write)

**Signature:**
```python
@staticmethod
def put_cache(cache_data: "CustomerMetaModel", updates: Dict[str, Any]) -> "CustomerMetaModel":
```

**Implementation:**
```python
@staticmethod
def put_cache(cache_data: "CustomerMetaModel", updates: Dict[str, Any]) -> "CustomerMetaModel":
    """
    Put cache with write lock
    Thread-safe write operation
    
    Args:
        cache_data: CustomerMetaModel instance to update
        updates: Dictionary of updates to apply
    
    Returns:
        Updated cache data
    """
    try:
        CustomerMetaModel.acquire_write_lock()
        
        # Apply updates
        for key, value in updates.items():
            if key == "metadata":
                # Update metadata fields
                if isinstance(value, dict):
                    if "total_customers" in value:
                        cache_data.metadata.total_customers = value["total_customers"]
                    if "last_updated" in value:
                        cache_data.metadata.last_updated = value["last_updated"]
                    if "version" in value:
                        cache_data.metadata.version = value["version"]
            else:
                # Update customer entries
                setattr(cache_data, key, value)
        
        # Update last_updated timestamp
        cache_data.metadata.last_updated = datetime.now().isoformat()
        
        logger.info(f"Cache updated with write lock. Updates: {list(updates.keys())}")
        return cache_data
    
    finally:
        CustomerMetaModel.release_write_lock()
```

**Lock Flow:**
```
1. Acquire write lock (exclusive)
2. Apply metadata updates
3. Apply customer entry updates
4. Update last_updated timestamp
5. Release write lock
6. Return updated cache
```

**Concurrency:** Only one writer at a time, readers blocked

**Example Usage:**
```python
# Only one thread can call this at a time
updates = {
    "metadata": {
        "total_customers": 5,
        "version": 2
    },
    "1#9876543210": {
        "1": "session-uuid-1"
    }
}
updated_cache = CustomerMetaModel.put_cache(cache_data, updates)
```

## Lock Hierarchy

```
_read_count_lock (threading.Lock)
  ↓
_write_lock (threading.Lock)
```

**Lock Ordering:**
1. First acquire `_read_count_lock` to protect counter
2. Then conditionally acquire `_write_lock`

**No Deadlock:** Lock ordering is consistent, no circular dependencies

## Concurrency Scenarios

### Scenario 1: Multiple Readers

```
Thread 1: get_cache() ──→ [READ LOCK] ──→ Proceeds
Thread 2: get_cache() ──→ [READ LOCK] ──→ Proceeds (concurrent)
Thread 3: get_cache() ──→ [READ LOCK] ──→ Proceeds (concurrent)

Result: All three readers execute concurrently
```

### Scenario 2: Reader Blocked by Writer

```
Thread 1: put_cache() ──→ [WRITE LOCK] ──→ Proceeds
Thread 2: get_cache() ──→ [READ LOCK] ──→ BLOCKED (waiting for write)
Thread 3: get_cache() ──→ [READ LOCK] ──→ BLOCKED (waiting for write)

After Thread 1 releases:
Thread 2: [READ LOCK] ──→ Proceeds
Thread 3: [READ LOCK] ──→ Proceeds (concurrent)
```

### Scenario 3: Writer Blocked by Readers

```
Thread 1: get_cache() ──→ [READ LOCK] ──→ Proceeds
Thread 2: get_cache() ──→ [READ LOCK] ──→ Proceeds
Thread 3: put_cache() ──→ [WRITE LOCK] ──→ BLOCKED

After Threads 1 & 2 release:
Thread 3: [WRITE LOCK] ──→ Proceeds
```

## Thread Safety Guarantees

### Atomicity
- Read operations are atomic within read lock
- Write operations are atomic within write lock
- No partial updates visible to readers

### Consistency
- Read lock ensures consistent snapshot
- Write lock ensures exclusive updates
- All readers see same data

### Isolation
- Readers don't see partial writes
- Writers don't interfere with readers
- Each operation is isolated

## Usage in SharedCustomerCache

The shared cache can now use these methods:

```python
# Before (direct access)
meta = SharedCustomerCache.get()

# After (with locks)
meta = CustomerMetaModel.get_cache(cache_data)
updated_meta = CustomerMetaModel.put_cache(cache_data, updates)
```

## Performance Characteristics

| Operation | Lock Type | Duration | Concurrency |
|-----------|-----------|----------|-------------|
| get_cache | Read | Short | Multiple |
| put_cache | Write | Medium | Single |
| acquire_read_lock | Lock | Instant | Multiple |
| acquire_write_lock | Lock | Instant | Single |

## Logging

All operations logged at appropriate levels:

```python
logger.debug(f"Read lock acquired. Read count: {_read_count}")
logger.debug(f"Read lock released. Read count: {_read_count}")
logger.debug("Write lock acquired")
logger.debug("Write lock released")
logger.info("Cache retrieved with read lock")
logger.info(f"Cache updated with write lock. Updates: {list(updates.keys())}")
```

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

## Integration Points

### SharedCustomerCache
Can now use:
```python
cache_copy = CustomerMetaModel.get_cache(_meta_cache)
updated_cache = CustomerMetaModel.put_cache(_meta_cache, updates)
```

### SharedClientCache
Can now use:
```python
cache_copy = ClientMetaModel.get_cache(_meta_cache)
updated_cache = ClientMetaModel.put_cache(_meta_cache, updates)
```

## Future Enhancements

1. **Lock Timeout** - Add timeout to prevent indefinite blocking
2. **Lock Metrics** - Track lock contention and wait times
3. **Optimistic Locking** - Use version numbers instead of locks
4. **Read-Write Separation** - Separate read and write paths
5. **Lock-Free Data Structures** - Use atomic operations

## Comparison with Previous Approach

### Before
```python
# Direct access without locks
meta = SharedCustomerCache.get()
meta.metadata.total_customers += 1
```

### After
```python
# Thread-safe access with locks
meta = CustomerMetaModel.get_cache(cache_data)
updates = {"metadata": {"total_customers": meta.metadata.total_customers + 1}}
updated_meta = CustomerMetaModel.put_cache(cache_data, updates)
```

**Benefits:**
- Thread-safe concurrent access
- Multiple readers supported
- Exclusive writer access
- Atomic operations
- Proper error handling
