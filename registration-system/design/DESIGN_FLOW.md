# High-Level Design Flow - Salon Prototype 2 Core System

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE SYSTEM FLOW                             │
└─────────────────────────────────────────────────────────────────────────┘

1. USER/CLIENT REQUEST (Async)
   ├─ Input: phone="9876543210", name="John Doe", task="CREATE-CUSTOMER"
   ├─ Endpoint: POST /customer/create
   └─ Request queued for async processing

2. UNIVERSAL CACHE (Shared across all parallel sessions)
   ├─ Initialize with Read-Write Lock mechanism
   ├─ Load metadata.json from DataModels/CustomerSchema/Schema/
   ├─ Multiple readers can access simultaneously
   ├─ Writers get exclusive access (all readers/writers wait)
   ├─ Readers wait for writers to complete
   └─ Ready for concurrent access

2A. UNIVERSAL CACHE OPERATIONS
   ├─ read(key)
   │  ├─ Acquire read lock (multiple readers allowed)
   │  ├─ Retrieve value from cache
   │  └─ Release read lock
   │
   ├─ read_all()
   │  ├─ Acquire read lock
   │  ├─ Return complete cache copy
   │  └─ Release read lock
   │
   ├─ write(key, value)
   │  ├─ Acquire write lock (exclusive - all wait)
   │  ├─ Update cache
   │  ├─ Save to metadata.json
   │  └─ Release write lock
   │
   ├─ update(key, updates)
   │  ├─ Acquire write lock (exclusive - all wait)
   │  ├─ Merge updates into existing entry
   │  ├─ Save to metadata.json
   │  └─ Release write lock
   │
   └─ delete(key)
      ├─ Acquire write lock (exclusive - all wait)
      ├─ Remove from cache
      ├─ Save to metadata.json
      └─ Release write lock

2B. METADATA MANAGER (Async - Uses Universal Cache)
   ├─ Load metadata from Universal Cache
   ├─ Initialize seq_counter from cached data
   └─ Ready for sequential ID generation

3. SESSION MANAGER (Async - Respects Lock Mechanism)
   ├─ create_session(phone) [Async]
   │  ├─ ACQUIRE READ LOCK on Universal Cache
   │  │  └─ Load metadata.json
   │  │
   │  ├─ Generate session_id (UUID)
   │  │
   │  ├─ Load metadata entry using key: phone
   │  │  └─ Example key: "9876543210"
   │  │
   │  ├─ RELEASE READ LOCK on Universal Cache
   │  │
   │  ├─ Store session metadata:
   │  │  {
   │  │    session_id: "uuid-xxx",
   │  │    phone: "9876543210",
   │  │    created_at: timestamp
   │  │  }
   │  │
   │  └─ Return: session_id
   │
   ├─ load_session(phone, data, task) [Async]
   │  ├─ ACQUIRE WRITE LOCK on Universal Cache
   │  │  └─ All parallel sessions wait here (respects lock)
   │  │  └─ Other requests continue to be queued
   │  │
   │  ├─ Load metadata from Universal Cache using key: phone
   │  │
   │  ├─ Call MetadataManager.generate_seq_id(phone, task)
   │  │  ├─ Read from Universal Cache (already locked)
   │  │  ├─ Increment seq_counter (sequential)
   │  │  ├─ Create mapping: {phone: {seq_id: version}}
   │  │  ├─ Update metadata entry: phone: {seq_id: version}
   │  │  ├─ Update Universal Cache
   │  │  ├─ Update metadata.json
   │  │  ├─ Update MAX_CUSTOMERS = seq_counter
   │  │  └─ Return: {seq_id, version, max_customers}
   │  │
   │  ├─ RELEASE WRITE LOCK on Universal Cache
   │  │  └─ Next parallel session proceeds (lock released)
   │  │
   │  ├─ Create session with seq_id
   │  ├─ Prepare: {session_id, seq_id, data, task, operation_type, phone}
   │  ├─ Add to QUEUE (thread-safe)
   │  └─ Return: {session_id, seq_id, phone} (non-blocking, immediate)
   │
   └─ destroy_session(session_id) [Async]
      └─ Remove session from memory

4. REQUEST QUEUE (Thread-safe - Async Processing)
   ├─ Multiple parallel requests queued here
   ├─ Each request waits for lock during metadata operations
   ├─ Once lock is released, request moves to execution queue
   └─ Item: {
        session_id: "uuid-xxx",
        seq_id: 1,
        phone: "9876543210",
        data: {phone, name},
        task: "CREATE-CUSTOMER",
        operation_type: "CREATE",
        version: 1,
        max_customers: 1
      }

5. EXECUTOR (Worker Thread Pool)
   ├─ Worker waits for queue item
   ├─ Retrieves item from queue
   │
   └─ PIPELINE EXECUTION (Sequential, waits for each step)
      │
      ├─ PHASE 1: LOAD
      │  ├─ Create session context
      │  ├─ Set status = LOADED
      │  └─ Return: {status: "LOADED", session_id} (JSON)
      │  └─ Thread waits for confirmation
      │
      ├─ PHASE 2: CACHE
      │  ├─ Store data in session
      │  ├─ Set status = CACHED
      │  └─ Return: {status: "CACHED", data_summary} (JSON)
      │  └─ Thread waits for confirmation
      │
      ├─ PHASE 3: VALIDATE
      │  ├─ Run validation rules
      │  ├─ Check schema compliance
      │  ├─ Set status = VALIDATED or FAILED
      │  └─ Return: {status: "VALIDATED", errors: []} (JSON)
      │  └─ Thread waits for confirmation
      │
      ├─ PHASE 4: PROCESS
      │  │
      │  ├─ 4A: API CALL (Optional, while session active)
      │  │  ├─ api_func(session_id, data)
      │  │  ├─ Can send/receive intermediate data
      │  │  └─ Return: {status: "API_SUCCESS", data} (JSON)
      │  │  └─ Thread waits for confirmation
      │  │
      │  ├─ 4B: EXECUTE ACTUAL ACTION
      │  │  ├─ If task = "CREATE-CUSTOMER"
      │  │  │  ├─ manager = CustomerManager(phone, name)
      │  │  │  ├─ customer_record = manager.create_customer()
      │  │  │  └─ Return: {customerId, status: "CREATED"} (JSON)
      │  │  │
      │  │  ├─ If task = "UPDATE-CUSTOMER"
      │  │  │  ├─ manager = CustomerManager(phone, name)
      │  │  │  ├─ customer_record = manager.update_customer()
      │  │  │  └─ Return: {customerId, version, status: "UPDATED"} (JSON)
      │  │  │
      │  │  └─ If task = "DELETE-CUSTOMER"
      │  │     ├─ manager = CustomerManager(phone, name)
      │  │     ├─ result = manager.delete_customer()
      │  │     └─ Return: {customerId, status: "DELETED"} (JSON)
      │  │
      │  │  └─ Thread waits for confirmation
      │  │
      │  └─ 4C: POST-ACTION SUB-FUNCTIONS (Optional)
      │     ├─ For each post_action_func in list:
      │     │  ├─ send_notification(customerId, "Welcome!")
      │     │  │  └─ Return: {status: "NOTIFICATION_SENT"} (JSON)
      │     │  │
      │     │  ├─ update_analytics(customerId, "CREATE")
      │     │  │  └─ Return: {status: "ANALYTICS_UPDATED"} (JSON)
      │     │  │
      │     │  ├─ log_audit(session_id, action, result)
      │     │  │  └─ Return: {status: "AUDIT_LOGGED"} (JSON)
      │     │  │
      │     │  └─ trigger_webhook(event, data)
      │     │     └─ Return: {status: "WEBHOOK_TRIGGERED"} (JSON)
      │     │
      │     └─ Thread waits for each sub-function
      │
      │  └─ Set status = PROCESSED
      │  └─ Return: {status: "PROCESSED", result} (JSON)
      │
      └─ PHASE 5: PERSIST
         ├─ Call WriteLive.write_customer(customer_record)
         ├─ Write to: src/data/stored_data/customer/live/{phone}.json
         ├─ Set status = PERSISTED
         └─ Return: {status: "PERSISTED", filepath} (JSON)
         └─ Thread waits for confirmation

6. SESSION UPDATE (End of Process - Lock & Update)
   ├─ ACQUIRE WRITE LOCK on Universal Cache
   │  └─ Exclusive access to metadata
   │
   ├─ Update metadata with final results:
   │  ├─ Add version entry: "{version}": "{session_id}"
   │  ├─ Update latest_version: latest_version = current_version
   │  └─ Example: "9876543210": {"1": "session-uuid-001", "latest_version": 1}
   │
   ├─ Update Universal Cache
   ├─ Save to metadata.json
   │
   ├─ RELEASE WRITE LOCK on Universal Cache
   │
   ├─ Update session with all phase results
   ├─ Final session object:
   │  {
   │    session_id: "uuid-xxx",
   │    seq_id: 1,
   │    phone: "9876543210",
   │    identifier: "9876543210",
   │    operation_type: "CREATE",
   │    status: "PERSISTED",
   │    version: 1,
   │    max_customers: 1,
   │    phases: {
   │      load: {status: "LOADED", timestamp},
   │      cache: {status: "CACHED", timestamp},
   │      validate: {status: "VALIDATED", timestamp},
   │      process: {
   │        api_call: {status: "API_SUCCESS"},
   │        action: {status: "CREATED", customerId},
   │        post_actions: [
   │          {notification: "SENT"},
   │          {analytics: "UPDATED"},
   │          {audit: "LOGGED"},
   │          {webhook: "TRIGGERED"}
   │        ]
   │      },
   │      persist: {status: "PERSISTED", filepath}
   │    },
   │    data: {...},
   │    errors: []
   │  }
   └─ destroy_session() called after completion

7. RESPONSE TO USER
   ├─ Poll endpoint: GET /session/{session_id}
   ├─ Returns: Final session object (JSON)
   └─ User gets complete execution history

8. THREADING MODEL (Async with Lock Respect)
   ├─ Main Thread: Handles incoming requests (non-blocking)
   ├─ Session Manager Thread: Async session creation & metadata management
   │  ├─ Respects Universal Cache locks
   │  ├─ Queues requests after lock release
   │  └─ Allows parallel requests to queue while waiting for lock
   │
   ├─ Worker Threads: Execute pipeline phases
   │  ├─ Process queued items sequentially
   │  └─ Each phase waits for previous to complete
   │
   ├─ Queue: Thread-safe communication
   │  ├─ Requests queue during metadata lock
   │  └─ Requests dequeue for pipeline execution
   │
   └─ Lock Mechanism:
      ├─ Read Lock: Multiple sessions can read metadata
      ├─ Write Lock: Exclusive access during seq_id generation
      └─ Parallel requests wait efficiently without blocking main thread
```

## Key Architectural Points

### Non-Blocking Design
- User gets `session_id` immediately
- Pipeline executes in background worker thread
- User can poll for results

### Sequential Phase Execution
- Each phase waits for previous phase to complete
- Every step returns JSON response
- Thread-safe queue for task distribution

### Optional Features
- **API Calls**: Send/receive data during processing
- **Post-Action Functions**: Execute after main action
  - Notifications
  - Analytics updates
  - Audit logging
  - Webhook triggers

### Thread Safety
- Queue: Thread-safe communication between main and worker threads
- Session Manager: Manages concurrent sessions
- Each worker thread processes one task at a time

### Complete Audit Trail
- Every phase tracked with timestamp
- All results stored in session object
- Error handling at each phase
- Final session contains complete execution history

## Universal Cache & Metadata Management Details

### Read-Write Lock Mechanism
```
Multiple Readers (Simultaneous Access):
Session 1 (Read)  ─┐
Session 2 (Read)  ─┼─→ All read simultaneously (no wait)
Session 3 (Read)  ─┘

Writer (Exclusive Access):
Session 4 (Write) ─→ WAIT for all readers ─→ EXCLUSIVE ACCESS ─→ All readers wait

Readers After Writer:
Session 5 (Read)  ─→ WAIT for writer ─→ Read after writer completes
```

### Universal Cache Operations
- **read(key)**: Multiple sessions can read simultaneously
- **write(key, value)**: Exclusive access, all sessions wait
- **update(key, updates)**: Exclusive access, all sessions wait
- **delete(key)**: Exclusive access, all sessions wait

### Metadata Structure
```json
{
  "9876543210": {
    "1": "session-uuid-001",
    "2": "session-uuid-002",
    "3": "session-uuid-003",
    "latest_version": 3
  },
  "9123456789": {
    "1": "session-uuid-004",
    "2": "session-uuid-005",
    "latest_version": 2
  }
}
```
- Key: Phone number
  - Example: "9876543210"
- Value: Object containing:
  - **Version number**: session_id (UUID)
    - Example: "1": "session-uuid-001"
  - **latest_version**: Integer tracking highest version
    - Example: "latest_version": 3
- Stored in Universal Cache
- Persisted to metadata.json after each write
- Updated at END of each process with lock
- Tracks all operations and current version for each phone number

### Sequential ID Generation (Thread-Safe with Write Lock)
```
Parallel Request 1 ─┐
                    ├─→ WRITE LOCK ACQUIRED ─→ seq_id = 1 ─→ LOCK RELEASED
Parallel Request 2 ─┤                                          ↓
                    └─→ WAIT ─→ WRITE LOCK ACQUIRED ─→ seq_id = 2 ─→ LOCK RELEASED
```

### MAX_CUSTOMERS Update
- Incremented with each sequential ID generation
- Reflects total customers created
- Updated atomically with write lock
- Persisted to metadata.json

## Parallel Request Processing Example

### Scenario: 3 Parallel Requests (1 CREATE + 2 UPDATE)

```
Timeline:

T1: Request 1 (Phone: 9876543210, Task: CREATE-CUSTOMER)
    ├─ create_session() → session_id_1
    ├─ load_session() → ACQUIRE WRITE LOCK ✓
    ├─ generate_seq_id() → seq_id=1 (NEW - only for CREATE)
    ├─ Update metadata: {"9876543210": {"1": "session_1", "latest_version": 1}}
    ├─ RELEASE WRITE LOCK
    └─ Add to Queue → Pipeline execution starts

T2: Request 2 (Phone: 9876543210, Task: UPDATE-CUSTOMER)
    ├─ create_session() → session_id_2
    ├─ load_session() → WAIT for WRITE LOCK (Request 1 has it)
    └─ [BLOCKED - waiting for lock]

T3: Request 3 (Phone: 9876543210, Task: UPDATE-CUSTOMER)
    ├─ create_session() → session_id_3
    ├─ load_session() → WAIT for WRITE LOCK (Request 1 has it)
    └─ [BLOCKED - waiting for lock]

T4: Request 1 completes metadata update
    ├─ RELEASE WRITE LOCK
    └─ Request 1 moves to Pipeline execution

T5: Request 2 acquires WRITE LOCK
    ├─ Read latest_version from metadata → latest_version=1
    ├─ Increment: next_version = 1 + 1 = 2 (NO new seq_id, just increment)
    ├─ Update metadata: {"9876543210": {"1": "session_1", "2": "session_2", "latest_version": 2}}
    ├─ RELEASE WRITE LOCK
    └─ Add to Queue → Pipeline execution starts

T6: Request 3 acquires WRITE LOCK
    ├─ Read latest_version from metadata → latest_version=2
    ├─ Increment: next_version = 2 + 1 = 3 (NO new seq_id, just increment)
    ├─ Update metadata: {"9876543210": {"1": "session_1", "2": "session_2", "3": "session_3", "latest_version": 3}}
    ├─ RELEASE WRITE LOCK
    └─ Add to Queue → Pipeline execution starts

T7-T9: All 3 requests execute in parallel in Pipeline
    ├─ Request 1 Pipeline: Load → Cache → Validate → Process → Persist
    ├─ Request 2 Pipeline: Load → Cache → Validate → Process → Persist
    └─ Request 3 Pipeline: Load → Cache → Validate → Process → Persist
```

### Key Points:

1. **CREATE Operation** (Generates new seq_id)
   - Request 1: Creates seq_id=1, latest_version=1

2. **UPDATE/DELETE Operations** (Use latest_version + 1)
   - Request 2: Uses latest_version (1) → increments to 2
   - Request 3: Uses latest_version (2) → increments to 3
   - No new seq_id generation, just version increment

3. **Final Metadata**
   ```json
   {
     "9876543210": {
       "1": "session_1",
       "2": "session_2",
       "3": "session_3",
       "latest_version": 3
     }
   }
   ```

4. **Benefits**
   - ✅ seq_id only created for CREATE (efficient)
   - ✅ UPDATE/DELETE reuse existing seq_id with version increment
   - ✅ Parallel pipeline execution (fast processing)
   - ✅ Lock held only during metadata update (minimal contention)
   - ✅ Requests don't block each other during pipeline

## File Structure
```
src/core/
├── pipeline.py              # Main pipeline orchestrator
├── session.py               # Session management
├── universal_cache.py       # Universal cache with read-write locking
├── metadata_manager.py      # Metadata & sequential ID management
├── executor.py              # Threading executor
├── queue_manager.py         # Queue management
├── storage.py               # Storage layer
├── DESIGN_FLOW.md          # This file
└── [management modules]/
    ├── customer_management/
    ├── client_management/
    └── appointment_management/
```

## Implementation Status
- [x] Universal Cache (read-write locking)
- [x] Session Manager (create, load, destroy)
- [x] Metadata Manager (sequential ID, thread-safe lock)
- [x] Pipeline (5 phases)
- [ ] Executor (threading)
- [ ] Queue Manager (thread-safe queue)
- [ ] API Call integration
- [ ] Post-action functions
