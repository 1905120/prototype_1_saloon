# Complete Workflow - Salon Prototype 2

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         REQUEST FLOW DIAGRAM                              │
└──────────────────────────────────────────────────────────────────────────┘

USER REQUEST
    ↓
    ├─→ POST /customer/create
    │   Body: {phone: "9876543210", name: "John Doe"}
    │
    ↓
MAIN THREAD (Non-blocking)
    ├─→ Receive request
    ├─→ Queue for async processing
    └─→ Return session_id immediately
    
    ↓
ASYNC SESSION CREATION
    ├─→ SessionManager.create_session(phone)
    │   ├─ ACQUIRE READ LOCK (UniversalCache)
    │   ├─ Generate session_id (UUID)
    │   ├─ Load metadata for phone
    │   ├─ RELEASE READ LOCK
    │   └─ Return session object
    │
    ↓
ASYNC METADATA MANAGEMENT
    ├─→ SessionManager.load_session(phone, data, task)
    │   ├─ ACQUIRE WRITE LOCK (UniversalCache)
    │   ├─ MetadataManager.generate_seq_id(phone, operation)
    │   │  ├─ If CREATE: seq_counter++ → seq_id = new
    │   │  └─ If UPDATE/DELETE: version = latest_version + 1
    │   ├─ MetadataManager.update_metadata(phone, seq_id, session_id, version)
    │   │  ├─ Add: "{version}": "{session_id}"
    │   │  ├─ Update: "latest_version": version
    │   │  └─ Save to metadata.json
    │   ├─ RELEASE WRITE LOCK
    │   └─ Add to REQUEST QUEUE
    │
    ↓
REQUEST QUEUE
    ├─→ Item: {
    │     session_id: "uuid-xxx",
    │     seq_id: 1,
    │     phone: "9876543210",
    │     data: {phone, name},
    │     task: "CREATE-CUSTOMER",
    │     operation_type: "CREATE",
    │     version: 1
    │   }
    │
    ↓
EXECUTOR (Worker Thread Pool)
    ├─→ Worker dequeues item
    ├─→ Call Pipeline.execute(queue_item, validators, processors, persisters)
    │
    ↓
PIPELINE EXECUTION (5 Phases)
    │
    ├─ PHASE 1: LOAD
    │  ├─ Initialize session context
    │  ├─ Set status = LOADED
    │  └─ Record timestamp
    │
    ├─ PHASE 2: CACHE
    │  ├─ Store data in session
    │  ├─ Set status = CACHED
    │  └─ Record timestamp
    │
    ├─ PHASE 3: VALIDATE
    │  ├─ Load schema from JSON
    │  ├─ Validate data against schema
    │  ├─ Run custom validators
    │  ├─ Set status = VALIDATED or FAILED
    │  └─ Record timestamp & errors
    │
    ├─ PHASE 4: PROCESS
    │  ├─ 4A: API Call (optional)
    │  │  └─ Call api_func(session_id, data)
    │  │
    │  ├─ 4B: Execute Business Logic
    │  │  ├─ If task = "CREATE-CUSTOMER"
    │  │  │  ├─ CustomerManager.create_customer()
    │  │  │  ├─ Generate customer record
    │  │  │  └─ Return: {customerId, status}
    │  │  │
    │  │  ├─ If task = "UPDATE-CUSTOMER"
    │  │  │  ├─ CustomerManager.update_customer()
    │  │  │  ├─ Update customer record
    │  │  │  └─ Return: {customerId, version, status}
    │  │  │
    │  │  └─ If task = "DELETE-CUSTOMER"
    │  │     ├─ CustomerManager.delete_customer()
    │  │     ├─ Soft delete customer
    │  │     └─ Return: {customerId, status}
    │  │
    │  ├─ 4C: Post-Action Functions (optional)
    │  │  ├─ send_notification(customerId, message)
    │  │  ├─ update_analytics(customerId, action)
    │  │  ├─ log_audit(session_id, action, result)
    │  │  └─ trigger_webhook(event, data)
    │  │
    │  ├─ Set status = PROCESSED
    │  └─ Record timestamp & results
    │
    └─ PHASE 5: PERSIST
       ├─ WriteLive.write_customer(customer_record)
       ├─ Write to: src/data/stored_data/customer/live/{phone}.json
       ├─ Set status = PERSISTED
       └─ Record timestamp & filepath
    
    ↓
FINAL METADATA UPDATE (with lock)
    ├─ ACQUIRE WRITE LOCK (UniversalCache)
    ├─ Update latest_version in metadata
    ├─ Save to metadata.json
    ├─ RELEASE WRITE LOCK
    └─ Close session
    
    ↓
USER POLLS FOR RESULT
    ├─ GET /session/{session_id}
    ├─ SessionManager.get_session(session_id)
    └─ Return: Complete session object with all phases
```

## Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPONENT INTERACTIONS                                │
└─────────────────────────────────────────────────────────────────────────┘

1. USER REQUEST
   └─→ main.py (entry point)

2. MAIN THREAD
   ├─→ SessionManager.create_session()
   │   └─→ UniversalCache.read() [READ LOCK]
   │
   └─→ SessionManager.load_session()
       ├─→ UniversalCache.acquire_write_lock()
       ├─→ MetadataManager.generate_seq_id()
       ├─→ MetadataManager.update_metadata()
       │   └─→ UniversalCache.update()
       ├─→ UniversalCache.release_write_lock()
       └─→ QueueManager.enqueue()

3. EXECUTOR (Background)
   ├─→ QueueManager.dequeue()
   └─→ Pipeline.execute()
       ├─→ Pipeline.load()
       ├─→ Pipeline.cache()
       ├─→ Pipeline.validate()
       │   └─→ Validator functions
       ├─→ Pipeline.process()
       │   ├─→ CustomerManager.create_customer()
       │   ├─→ Post-action functions
       │   └─→ API functions
       ├─→ Pipeline.persist()
       │   └─→ WriteLive.write_customer()
       └─→ Pipeline._update_final_metadata()
           └─→ UniversalCache.update() [WRITE LOCK]

4. USER POLLS
   └─→ SessionManager.get_session()
```

## Data Flow Through Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA TRANSFORMATION FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

INPUT DATA
{
  phone: "9876543210",
  name: "John Doe"
}
    ↓
PHASE 1: LOAD
{
  session_id: "uuid-xxx",
  phone: "9876543210",
  seq_id: 1,
  version: 1,
  status: "LOADED"
}
    ↓
PHASE 2: CACHE
{
  ...previous,
  data: {phone, name},
  status: "CACHED"
}
    ↓
PHASE 3: VALIDATE
{
  ...previous,
  validation_errors: [],
  status: "VALIDATED"
}
    ↓
PHASE 4: PROCESS
{
  ...previous,
  process_result: {
    api_call: {status: "API_SUCCESS"},
    action: {
      status: "SUCCESS",
      result: {customerId: "uuid-yyy", ...}
    },
    post_actions: [...]
  },
  status: "PROCESSED"
}
    ↓
PHASE 5: PERSIST
{
  ...previous,
  persist_result: {
    status: "SUCCESS",
    filepath: "src/data/stored_data/customer/live/9876543210.json"
  },
  status: "PERSISTED"
}
    ↓
FINAL SESSION OBJECT
{
  session_id: "uuid-xxx",
  seq_id: 1,
  phone: "9876543210",
  version: 1,
  status: "PERSISTED",
  phases: {
    load: {status, timestamp},
    cache: {status, timestamp},
    validate: {status, timestamp, errors},
    process: {status, timestamp, result},
    persist: {status, timestamp, result}
  },
  data: {...},
  errors: []
}
```

## Parallel Request Handling

```
┌─────────────────────────────────────────────────────────────────────────┐
│              PARALLEL REQUESTS WITH LOCK MANAGEMENT                      │
└─────────────────────────────────────────────────────────────────────────┘

REQUEST 1 (CREATE)          REQUEST 2 (UPDATE)          REQUEST 3 (UPDATE)
    ↓                           ↓                            ↓
create_session()            create_session()            create_session()
    ↓                           ↓                            ↓
load_session()              load_session()              load_session()
    ↓                           ↓                            ↓
WRITE LOCK ✓                WRITE LOCK ⏳                WRITE LOCK ⏳
    ↓                           ↓                            ↓
seq_id=1                    WAIT...                     WAIT...
version=1                       ↓                            ↓
    ↓                       WRITE LOCK ✓                WRITE LOCK ⏳
RELEASE LOCK                    ↓                            ↓
    ↓                       version=2                   WAIT...
QUEUE                       (latest+1)                      ↓
    ↓                           ↓                       WRITE LOCK ✓
Pipeline Start              RELEASE LOCK                    ↓
    ↓                           ↓                       version=3
Load → Cache →              QUEUE                       (latest+1)
Validate →                      ↓                           ↓
Process →                   Pipeline Start              RELEASE LOCK
Persist                         ↓                           ↓
    ↓                       Load → Cache →              QUEUE
FINAL METADATA              Validate →                      ↓
UPDATE                      Process →                   Pipeline Start
    ↓                       Persist                         ↓
COMPLETE                        ↓                       Load → Cache →
                            FINAL METADATA              Validate →
                            UPDATE                      Process →
                                ↓                       Persist
                            COMPLETE                        ↓
                                                        FINAL METADATA
                                                        UPDATE
                                                            ↓
                                                        COMPLETE

FINAL METADATA:
{
  "9876543210": {
    "1": "session_1",
    "2": "session_2",
    "3": "session_3",
    "latest_version": 3
  }
}
```

## Key Workflow Characteristics

1. **Non-Blocking**: User gets session_id immediately
2. **Async Processing**: All work happens in background
3. **Thread-Safe**: Locks ensure data consistency
4. **Sequential IDs**: CREATE generates new, UPDATE/DELETE increment
5. **Parallel Execution**: Multiple requests process simultaneously
6. **Complete Audit**: Every step tracked with timestamps
7. **Error Handling**: Errors caught and recorded at each phase
8. **Persistence**: Data written to live storage
9. **Metadata Tracking**: All operations recorded in metadata.json

## Next: Business Logic Implementation

The workflow is ready for business logic integration:
- CustomerManager (CREATE, UPDATE, DELETE)
- Validators (schema, business rules)
- Processors (business logic execution)
- Persisters (data storage)
- Post-action functions (notifications, analytics, etc.)
