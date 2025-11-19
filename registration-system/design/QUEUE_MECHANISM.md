# Queue Mechanism Analysis

## Architecture Overview

The queue mechanism integrates three key components:

### 1. **OperationWorker** (`src/core/worker.py`)
- Manages a thread-safe operation queue
- Processes operations through the DataPipeline
- Stores results by session_id
- Runs as a background daemon thread

**Key Methods:**
- `queue_operation(operation)` - Adds operation to queue
- `start()` - Starts worker thread
- `stop()` - Gracefully stops worker thread
- `get_result(session_id, timeout)` - Retrieves operation result
- `_worker_loop()` - Main processing loop
- `_process_operation(operation)` - Executes operation through pipeline

### 2. **WorkerManager** (`src/core/worker_manager.py`)
- Singleton pattern for global worker instance
- Initialized at application startup
- Thread-safe access to worker
- Provides queue and result retrieval interface

**Key Methods:**
- `initialize(universal_cache)` - Creates and starts global worker
- `get()` - Returns global worker instance
- `queue_operation(operation)` - Queues operation globally
- `get_result(session_id, timeout)` - Gets result globally
- `shutdown()` - Stops global worker

### 3. **DataPipeline** (`src/core/pipeline.py`)
- Orchestrates 5-phase processing:
  1. **Load** - Initialize session
  2. **Cache** - Store data in session
  3. **Validate** - Validate cached data
  4. **Process** - Execute business logic
  5. **Persist** - Write to storage

## Flow Diagram

```
Request
  ↓
route_salon_request (src/business/salon/api.py)
  ↓
Handler (create_customer, update_customer, etc.)
  ↓
WorkerManager.queue_operation()
  ↓
OperationWorker.operation_queue
  ↓
Worker Thread (_worker_loop)
  ↓
_process_operation()
  ↓
DataPipeline.execute()
  ├─ Load Phase
  ├─ Cache Phase
  ├─ Validate Phase
  ├─ Process Phase (_execute_operation)
  └─ Persist Phase (_persist_operation)
  ↓
Result stored in OperationWorker.results[session_id]
  ↓
Client polls get_result(session_id) or waits with timeout
```

## Operation Structure

```python
operation = {
    "type": "CREATE|UPDATE|DELETE",
    "session_id": "uuid",
    "data": {
        "phone": "...",
        "name": "...",
        ...
    },
    "business_context": BusinessContext,
    "entity_context": CustomerContext|ClientContext
}
```

## Thread Safety

- **OperationWorker.operation_queue** - Thread-safe queue.Queue()
- **OperationWorker.results** - Protected by operation_queue.get/put atomicity
- **WorkerManager._worker_lock** - Protects singleton initialization
- **DataPipeline** - Uses UniversalCache with read/write locks

## Lifecycle

### Startup (main.py)
```python
@app.on_event("startup")
async def startup_event():
    business_cache = get_universal_cache("DataModels/Salon/salon_meta.json")
    WorkerManager.initialize(business_cache)  # Creates and starts worker
```

### Request Processing
```python
# Handler queues operation
session_id = WorkerManager.queue_operation(operation)

# Return immediately with session_id
return SessionResponse(session_id=session_id, status="QUEUED")

# Client can poll for result
result = WorkerManager.get_result(session_id, timeout=30)
```

### Shutdown (main.py)
```python
@app.on_event("shutdown")
async def shutdown_event():
    WorkerManager.shutdown()  # Stops worker thread
```

## Key Features

1. **Asynchronous Processing** - Operations processed in background thread
2. **Session Tracking** - Each operation has unique session_id
3. **Result Storage** - Results stored until retrieved
4. **Pipeline Integration** - Full 5-phase processing for each operation
5. **Context Passing** - Business and entity contexts passed through pipeline
6. **Error Handling** - Errors captured and stored with session
7. **Graceful Shutdown** - Worker thread joins with timeout on shutdown

## Integration Points

### Salon API (src/business/salon/api.py)
- Handlers receive business_context and entity_context
- Queue operations via WorkerManager
- Return session_id for client tracking

### Context Setup (src/checkbusiness.py)
- Creates BusinessContext from business metadata
- Creates CustomerContext or ClientContext based on phone mapping
- Passes both contexts to route_salon_request

### Managers (src/core/customer_management/manager.py, src/core/client_management/manager.py)
- Implement business logic for CREATE, UPDATE, DELETE
- Called by OperationWorker._execute_operation()
- Results persisted by OperationWorker._persist_operation()
