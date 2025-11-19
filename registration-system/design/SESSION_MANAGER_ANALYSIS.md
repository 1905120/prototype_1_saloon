# SessionManager Analysis

## Overview

The `SessionManager` is the core component that manages the lifecycle of individual operations/requests. It works in conjunction with `UniversalCache`, `MetadataManager`, and the `DataPipeline` to provide thread-safe, versioned session management.

## Architecture

```
SessionManager
├── sessions: Dict[session_id → session_object]
├── cache: UniversalCache (shared, singleton)
└── metadata_manager: MetadataManager
    └── cache: UniversalCache
```

## Session Object Structure

```python
session = {
    "session_id": "uuid",                    # Unique identifier
    "phone": "9876543210",                   # Customer/client phone
    "operation_type": "CREATE|UPDATE|DELETE", # Operation type
    "status": "LOADED|CACHED|VALIDATED|PROCESSED|PERSISTED|FAILED",
    "created_at": "2024-11-17T...",         # Creation timestamp
    "data": {...},                           # Operation data
    "validation_errors": [],                 # Validation errors if any
    "process_result": {...},                 # Result from processing
    "error": None,                           # Error message if failed
    "seq_id": 1,                            # Sequential ID (for versioning)
    "version": 1,                            # Version number
    "metadata": {...},                       # Metadata snapshot at creation
    "phases": {                              # Phase tracking
        "load": {...},
        "cache": {...},
        "validate": {...},
        "process": {...},
        "persist": {...}
    }
}
```

## Key Methods

### 1. `create_session(phone, operation_type)`

**Purpose:** Initialize a new session with read lock

**Flow:**
```
1. Acquire READ lock on UniversalCache
2. Generate unique session_id (UUID)
3. Load metadata for phone from cache
4. Create session object with initial state
5. Store in self.sessions[session_id]
6. Release READ lock
7. Return session
```

**Thread Safety:**
- Uses `cache.acquire_read_lock()` to safely read metadata
- Multiple readers can execute simultaneously
- Metadata snapshot captured at session creation

**Example:**
```python
session = session_manager.create_session(
    phone="9876543210",
    operation_type=OperationType.CREATE
)
# Returns session with status=LOADED
```

### 2. `load_session(phone, data, task, operation_type)`

**Purpose:** Load session with metadata update and seq_id generation

**Flow:**
```
1. Call create_session() to initialize
2. Acquire WRITE lock on UniversalCache
3. Generate seq_id and version via MetadataManager
4. Update metadata with new session mapping
5. Update session with seq_id, version, data
6. Release WRITE lock
7. Return updated session
```

**Thread Safety:**
- Uses `cache.acquire_write_lock()` for exclusive access
- Only one writer at a time
- Readers blocked during write
- Try-finally ensures lock release even on error

**Example:**
```python
session = session_manager.load_session(
    phone="9876543210",
    data={"name": "John Doe"},
    task="CREATE-CUSTOMER",
    operation_type=OperationType.CREATE
)
# Returns session with seq_id, version, and updated metadata
```

### 3. `get_session(session_id)`

**Purpose:** Retrieve session by ID

**Implementation:**
```python
def get_session(self, session_id: str) -> Dict[str, Any]:
    if session_id not in self.sessions:
        ErrorHandler.raise_session_not_found(session_id)
    return self.sessions[session_id]
```

**Note:** No locking needed - in-memory dictionary access

### 4. `update_session(session_id, updates)`

**Purpose:** Update session with new data

**Implementation:**
```python
def update_session(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    session = self.get_session(session_id)
    session.update(updates)
    return session
```

### 5. `set_session_status(session_id, status)`

**Purpose:** Update session pipeline status

**Used by DataPipeline:**
```python
# In DataPipeline.load()
self.session_manager.set_session_status(session_id, PipelineStatus.LOADED)

# In DataPipeline.cache()
self.session_manager.set_session_status(session_id, PipelineStatus.CACHED)

# In DataPipeline.validate()
self.session_manager.set_session_status(session_id, PipelineStatus.VALIDATED)

# In DataPipeline.process()
self.session_manager.set_session_status(session_id, PipelineStatus.PROCESSED)

# In DataPipeline.persist()
self.session_manager.set_session_status(session_id, PipelineStatus.PERSISTED)
```

### 6. `set_session_data(session_id, data)`

**Purpose:** Set session data

**Implementation:**
```python
def set_session_data(self, session_id: str, data: Dict[str, Any]) -> None:
    session = self.get_session(session_id)
    session["data"] = data
```

### 7. `close_session(session_id)`

**Purpose:** Clean up session after completion

**Implementation:**
```python
def close_session(self, session_id: str) -> None:
    if session_id in self.sessions:
        del self.sessions[session_id]
```

## Integration with UniversalCache

### Read-Write Lock Mechanism

**UniversalCache implements a reader-writer lock:**

```
Multiple Readers:
  Reader 1 ─┐
  Reader 2 ─┼─→ [Read Lock] ─→ Read from cache
  Reader 3 ─┘

Single Writer:
  Writer ──→ [Write Lock] ─→ Write to cache (blocks readers)
```

**Lock Implementation:**
```python
# Read Lock
def acquire_read_lock(self):
    with self.read_count_lock:
        self.read_count += 1
        if self.read_count == 1:
            self.write_lock.acquire()  # Block writers

def release_read_lock(self):
    with self.read_count_lock:
        self.read_count -= 1
        if self.read_count == 0:
            self.write_lock.release()  # Allow writers

# Write Lock
def acquire_write_lock(self):
    self.write_lock.acquire()  # Exclusive access

def release_write_lock(self):
    self.write_lock.release()
```

## Integration with MetadataManager

### Metadata Update Flow

```
SessionManager.load_session()
  ↓
acquire_write_lock()
  ↓
MetadataManager.generate_seq_id()
  ├─ Reads current seq_counter
  ├─ Increments counter
  └─ Returns seq_id and version
  ↓
MetadataManager.update_metadata()
  ├─ Reads existing metadata for phone
  ├─ Adds version → session_id mapping
  ├─ Updates latest_version
  └─ Writes back to cache
  ↓
release_write_lock()
```

## Integration with DataPipeline

### Session Lifecycle Through Pipeline

```
1. LOAD Phase
   ├─ SessionManager.create_session()
   ├─ Status: LOADED
   └─ Metadata snapshot captured

2. CACHE Phase
   ├─ SessionManager.set_session_data()
   ├─ Status: CACHED
   └─ Data stored in session

3. VALIDATE Phase
   ├─ Validate session data
   ├─ Status: VALIDATED or FAILED
   └─ Errors stored if validation fails

4. PROCESS Phase
   ├─ Execute business logic
   ├─ Status: PROCESSED
   └─ Result stored in session

5. PERSIST Phase
   ├─ Write to storage
   ├─ Status: PERSISTED
   └─ SessionManager._update_final_metadata()
       ├─ Acquire write lock
       ├─ Update latest_version in metadata
       └─ Release write lock
```

## Thread Safety Guarantees

### 1. Session Isolation
- Each session has unique session_id
- Sessions stored in separate dictionary entries
- No cross-session interference

### 2. Metadata Consistency
- Read operations use read lock (multiple concurrent readers)
- Write operations use write lock (exclusive access)
- Metadata updates atomic within write lock

### 3. Version Tracking
- seq_id generated atomically within write lock
- Version incremented per operation
- Metadata stores version → session_id mapping

### 4. Lock Ordering
- Always acquire locks in same order: read_lock → write_lock
- Prevents deadlock scenarios
- Try-finally ensures lock release

## Concurrency Scenarios

### Scenario 1: Multiple CREATE operations for different phones

```
Thread 1: create_session(phone="111") ─→ [Read Lock] ─→ session_1
Thread 2: create_session(phone="222") ─→ [Read Lock] ─→ session_2
Thread 3: create_session(phone="333") ─→ [Read Lock] ─→ session_3

Result: All execute concurrently (multiple readers)
```

### Scenario 2: CREATE and UPDATE for same phone

```
Thread 1: load_session(phone="111", CREATE) ─→ [Write Lock] ─→ seq_id=1
Thread 2: load_session(phone="111", UPDATE) ─→ [Waiting...] ─→ seq_id=2

Result: Sequential execution (write lock exclusive)
```

### Scenario 3: Multiple reads during write

```
Thread 1: load_session() ─→ [Write Lock acquired]
Thread 2: create_session() ─→ [Waiting for write lock]
Thread 3: create_session() ─→ [Waiting for write lock]

After Thread 1 releases:
Thread 2: [Read Lock acquired] ─→ Proceeds
Thread 3: [Read Lock acquired] ─→ Proceeds

Result: Write completes first, then readers proceed
```

## Error Handling

### Session Not Found
```python
def get_session(self, session_id: str):
    if session_id not in self.sessions:
        ErrorHandler.raise_session_not_found(session_id)
```

### Lock Release on Error
```python
def load_session(self, ...):
    try:
        # ... operations ...
    except:
        self.cache.release_write_lock()  # Release on error
    finally:
        self.cache.release_write_lock()  # Always release
```

## Performance Characteristics

| Operation | Lock Type | Concurrency | Time Complexity |
|-----------|-----------|-------------|-----------------|
| create_session | Read | Multiple | O(1) |
| load_session | Write | Single | O(1) |
| get_session | None | Multiple | O(1) |
| update_session | None | Multiple | O(1) |
| set_session_status | None | Multiple | O(1) |
| close_session | None | Multiple | O(1) |

## Best Practices

1. **Always use try-finally for locks**
   ```python
   self.cache.acquire_write_lock()
   try:
       # operations
   finally:
       self.cache.release_write_lock()
   ```

2. **Minimize lock hold time**
   - Only hold locks during critical sections
   - Release immediately after operation

3. **Use appropriate lock type**
   - Read lock for metadata reads
   - Write lock for metadata updates

4. **Handle errors gracefully**
   - Catch exceptions within lock scope
   - Ensure locks released in finally block

5. **Session cleanup**
   - Call close_session() after pipeline completion
   - Prevents memory leaks in long-running applications
