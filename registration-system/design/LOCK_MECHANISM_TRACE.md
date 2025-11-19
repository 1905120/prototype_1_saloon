# Lock Mechanism Trace - Session and Cache Operations

## Overview

This document traces where locks are acquired and released during session creation and loading operations. There are two levels of locking:

1. **UniversalCache Locks** - For business context cache
2. **SharedCache Locks** - For customer/client specific caches

## Session Creation Flow with Locks

### Operation: `SessionManager.create_session(phone, operation_type)`

**Location:** `src/core/session.py` - Lines 33-67

```python
def create_session(self, phone: str, operation_type: OperationType) -> Dict[str, Any]:
    # ============ ACQUIRE READ LOCK ============
    self.cache.acquire_read_lock()  # Line 37
    try:
        session_id = str(uuid.uuid4())
        
        # Load metadata for phone (within read lock)
        metadata = self.cache.read(phone)  # Line 41
        
        session = {
            "session_id": session_id,
            "phone": phone,
            "operation_type": operation_type.value,
            "status": PipelineStatus.LOADED.value,
            "created_at": datetime.now().isoformat(),
            "data": None,
            "validation_errors": [],
            "process_result": None,
            "error": None,
            "seq_id": None,
            "version": None,
            "metadata": metadata
        }
        
        self.sessions[session_id] = session
        return session
    finally:
        # ============ RELEASE READ LOCK ============
        self.cache.release_read_lock()  # Line 65
```

**Lock Details:**
- **Type:** READ LOCK (UniversalCache)
- **Acquired at:** Line 37
- **Released at:** Line 65 (in finally block)
- **Duration:** Entire session creation
- **Concurrency:** Multiple readers allowed

## Session Loading Flow with Locks

### Operation: `SessionManager.load_session(phone, data, task, operation_type)`

**Location:** `src/core/session.py` - Lines 69-155

#### Step 1: Create Session (with read lock)
```python
def load_session(self, phone, data, task, operation_type):
    try:
        # Create session first (uses read lock internally)
        session = self.create_session(phone, operation_type)
        # ↓ READ LOCK acquired and released here
```

#### Step 2: Create or Get Customer (with write lock)
```python
        if self.entity_type == "customer":
            from src.core.customer_management.shared import SharedCustomerCache
            
            # ============ ACQUIRE WRITE LOCK (SharedCustomerCache) ============
            customer_data = SharedCustomerCache.create_or_get_customer(phone)
            # ↓ WRITE LOCK acquired inside this method
            # ↓ WRITE LOCK released inside this method
            
            seq_id = customer_data["seq_id"]
            is_new = customer_data["created"]
            
            existing_sessions = customer_data.get("sessions", {})
            version = len(existing_sessions) + 1
            
            # ============ ACQUIRE WRITE LOCK (SharedCustomerCache) ============
            SharedCustomerCache.add_customer_session(seq_id, phone, version, session["session_id"])
            # ↓ WRITE LOCK acquired inside this method
            # ↓ WRITE LOCK released inside this method
```

#### Step 3: Update Session
```python
        # Update session with seq_id and version (no lock needed - in-memory)
        session["seq_id"] = seq_id
        session["version"] = version
        session["data"] = data
        
        return session
    except Exception as e:
        logger.error(f"Failed to load session: {str(e)}", exc_info=True)
        raise
```

## UniversalCache Lock Implementation

### Read Lock Mechanism

**Location:** `src/core/universal_cache.py` - Lines 213-225

```python
def acquire_read_lock(self) -> None:
    """Acquire read lock - multiple readers allowed"""
    with self.read_count_lock:  # Protect read_count
        self.read_count += 1
        if self.read_count == 1:
            self.write_lock.acquire()  # Block writers on first reader

def release_read_lock(self) -> None:
    """Release read lock"""
    with self.read_count_lock:  # Protect read_count
        self.read_count -= 1
        if self.read_count == 0:
            self.write_lock.release()  # Allow writers when no readers
```

**Lock Hierarchy:**
```
read_count_lock (threading.Lock)
  ↓
write_lock (threading.Lock)
```

### Write Lock Mechanism

**Location:** `src/core/universal_cache.py` - Lines 227-232

```python
def acquire_write_lock(self) -> None:
    """Acquire write lock - exclusive access"""
    self.write_lock.acquire()  # Exclusive access

def release_write_lock(self) -> None:
    """Release write lock"""
    self.write_lock.release()
```

## SharedCustomerCache Lock Implementation

### Create or Get Customer (Write Lock)

**Location:** `src/core/customer_management/shared.py` - Lines 195-240

```python
@staticmethod
def create_or_get_customer(phone: str) -> Dict[str, Any]:
    # ============ ACQUIRE WRITE LOCK ============
    with _meta_lock:  # threading.Lock()
        if _meta_cache is None:
            _meta_cache = SharedCustomerCache._load_from_file()
        
        # Check if customer exists (read within lock)
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
        
        # Save to file (atomic write)
        SharedCustomerCache._save_to_file(_meta_cache)
        
        return {
            "seq_id": seq_id,
            "phone": phone,
            "sessions": {},
            "created": True
        }
    # ============ RELEASE WRITE LOCK ============
```

**Lock Details:**
- **Type:** WRITE LOCK (threading.Lock)
- **Acquired at:** `with _meta_lock:`
- **Released at:** End of `with` block
- **Duration:** Entire create_or_get operation
- **Concurrency:** Single exclusive access

### Add Customer Session (Write Lock)

**Location:** `src/core/customer_management/shared.py` - Lines 113-130

```python
@staticmethod
def add_customer_session(seq_id: int, phone: str, version: int, session_id: str) -> None:
    # ============ ACQUIRE WRITE LOCK ============
    with _meta_lock:  # threading.Lock()
        if _meta_cache is None:
            _meta_cache = SharedCustomerCache._load_from_file()
        
        customer_key = f"{seq_id}#{phone}"
        
        if not hasattr(_meta_cache, customer_key):
            setattr(_meta_cache, customer_key, {})
        
        customer_data = getattr(_meta_cache, customer_key)
        customer_data[str(version)] = session_id
        
        # Save to file (atomic write)
        SharedCustomerCache._save_to_file(_meta_cache)
        
        logger.info(f"Added customer session: {seq_id}#{phone} v{version} → {session_id}")
    # ============ RELEASE WRITE LOCK ============
```

## Complete Lock Sequence Diagram

```
route_salon_request()
  │
  ├─ SessionManager.load_session()
  │  │
  │  ├─ SessionManager.create_session()
  │  │  │
  │  │  ├─ [ACQUIRE READ LOCK - UniversalCache]
  │  │  ├─ cache.acquire_read_lock()
  │  │  ├─ cache.read(phone)
  │  │  ├─ [RELEASE READ LOCK - UniversalCache]
  │  │  └─ cache.release_read_lock()
  │  │
  │  ├─ SharedCustomerCache.create_or_get_customer(phone)
  │  │  │
  │  │  ├─ [ACQUIRE WRITE LOCK - SharedCustomerCache]
  │  │  ├─ with _meta_lock:
  │  │  ├─ Check if customer exists
  │  │  ├─ If not, create new customer
  │  │  ├─ Increment total_customers
  │  │  ├─ Save to file
  │  │  ├─ [RELEASE WRITE LOCK - SharedCustomerCache]
  │  │  └─ return customer_data
  │  │
  │  └─ SharedCustomerCache.add_customer_session()
  │     │
  │     ├─ [ACQUIRE WRITE LOCK - SharedCustomerCache]
  │     ├─ with _meta_lock:
  │     ├─ Add session mapping
  │     ├─ Save to file
  │     ├─ [RELEASE WRITE LOCK - SharedCustomerCache]
  │     └─ return
  │
  └─ Return session with seq_id and version
```

## Lock Timing Analysis

### Scenario 1: New Customer Creation

```
Time  Operation                          Lock Status
────  ─────────────────────────────────  ──────────────────────
T0    create_session()                   
T1    acquire_read_lock()                [READ LOCK ACQUIRED]
T2    cache.read(phone)                  [READ LOCK HELD]
T3    release_read_lock()                [READ LOCK RELEASED]
T4    create_or_get_customer()           
T5    acquire _meta_lock                 [WRITE LOCK ACQUIRED]
T6    Check if customer exists           [WRITE LOCK HELD]
T7    Create new customer                [WRITE LOCK HELD]
T8    Increment total_customers          [WRITE LOCK HELD]
T9    Save to file                       [WRITE LOCK HELD]
T10   release _meta_lock                 [WRITE LOCK RELEASED]
T11   add_customer_session()             
T12   acquire _meta_lock                 [WRITE LOCK ACQUIRED]
T13   Add session mapping                [WRITE LOCK HELD]
T14   Save to file                       [WRITE LOCK HELD]
T15   release _meta_lock                 [WRITE LOCK RELEASED]
T16   Return session
```

### Scenario 2: Existing Customer Update

```
Time  Operation                          Lock Status
────  ─────────────────────────────────  ──────────────────────
T0    create_session()                   
T1    acquire_read_lock()                [READ LOCK ACQUIRED]
T2    cache.read(phone)                  [READ LOCK HELD]
T3    release_read_lock()                [READ LOCK RELEASED]
T4    create_or_get_customer()           
T5    acquire _meta_lock                 [WRITE LOCK ACQUIRED]
T6    Check if customer exists           [WRITE LOCK HELD]
T7    Customer found! Return existing    [WRITE LOCK HELD]
T8    release _meta_lock                 [WRITE LOCK RELEASED]
T9    add_customer_session()             
T10   acquire _meta_lock                 [WRITE LOCK ACQUIRED]
T11   Add session mapping                [WRITE LOCK HELD]
T12   Save to file                       [WRITE LOCK HELD]
T13   release _meta_lock                 [WRITE LOCK RELEASED]
T14   Return session
```

## Concurrency Scenarios

### Scenario A: Multiple Readers (create_session)

```
Thread 1: create_session() ──→ [READ LOCK] ──→ Proceeds
Thread 2: create_session() ──→ [READ LOCK] ──→ Proceeds (concurrent)
Thread 3: create_session() ──→ [READ LOCK] ──→ Proceeds (concurrent)

Result: All three readers execute concurrently
```

### Scenario B: Reader Blocked by Writer

```
Thread 1: create_or_get_customer() ──→ [WRITE LOCK] ──→ Proceeds
Thread 2: create_session() ──→ [READ LOCK] ──→ BLOCKED (waiting for write)
Thread 3: create_session() ──→ [READ LOCK] ──→ BLOCKED (waiting for write)

After Thread 1 releases:
Thread 2: [READ LOCK] ──→ Proceeds
Thread 3: [READ LOCK] ──→ Proceeds (concurrent)
```

### Scenario C: Writer Blocked by Readers

```
Thread 1: create_session() ──→ [READ LOCK] ──→ Proceeds
Thread 2: create_session() ──→ [READ LOCK] ──→ Proceeds
Thread 3: create_or_get_customer() ──→ [WRITE LOCK] ──→ BLOCKED

After Threads 1 & 2 release:
Thread 3: [WRITE LOCK] ──→ Proceeds
```

## Lock Guarantees

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

| Operation | Lock Type | Duration | Concurrency |
|-----------|-----------|----------|-------------|
| create_session | Read | Short | Multiple |
| create_or_get_customer | Write | Medium | Single |
| add_customer_session | Write | Medium | Single |
| Total load_session | Mixed | Long | Sequential |

## Potential Deadlock Analysis

### Lock Ordering
1. UniversalCache read_lock (if used)
2. SharedCache _meta_lock

**No deadlock possible** because:
- Only one lock type acquired per operation
- No nested lock acquisition
- Locks always released in finally blocks

## Future Improvements

1. **Lock Timeout** - Add timeout to prevent indefinite blocking
2. **Lock Metrics** - Track lock contention and wait times
3. **Optimistic Locking** - Use version numbers instead of locks
4. **Read-Write Separation** - Separate read and write paths
5. **Lock-Free Data Structures** - Use atomic operations
