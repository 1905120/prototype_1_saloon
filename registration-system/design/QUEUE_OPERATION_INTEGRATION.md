# Queue Operation Integration - Background Processing

## Overview

Updated `create_customer` handler to queue operations for background processing via `WorkerManager`. Instead of executing immediately, operations are queued and processed by worker threads, allowing the API to respond quickly while work continues in the background.

## Implementation

### Operation Structure

```python
operation = {
    "type": "CREATE",                           # Operation type
    "session_id": session["session_id"],        # Session identifier
    "seq_id": session.get("seq_id"),           # Sequential ID
    "version": session.get("version"),         # Version number
    "data": payload.data,                       # Request data
    "business_context": business_context,       # Business context
    "entity_context": entity_context,           # Entity context
    "action": "CREATE-CUSTOMER",                # Action name
    "timestamp": datetime.now().isoformat()     # Operation timestamp
}
```

### Queue Operation Flow

```python
# Queue the operation via WorkerManager
queued_session_id = WorkerManager.queue_operation(operation)
logger.info(f"Queued CREATE-CUSTOMER operation: session_id={queued_session_id}, phone={payload.phone}")
```

### Response

**Before (Synchronous):**
```python
return SessionResponse(
    session_id=session["session_id"],
    status="COMPLETED",
    message="Customer creation completed"
)
```

**After (Asynchronous):**
```python
return SessionResponse(
    session_id=session["session_id"],
    status="QUEUED",
    message="Customer creation queued for processing"
)
```

## Complete Handler Implementation

```python
async def create_customer(payload: MainRequest, background_tasks: BackgroundTasks, business_context, entity_context, session: Dict[str, Any]) -> SessionResponse:
    """Create a new customer"""
    if not payload.phone or not payload.name or not payload.business:
        raise HTTPException(status_code=400, detail="phone, name, and business are required")
    
    try:
        logger.info(f"Creating customer with phone: {payload.phone}, session: {session['session_id']}")
        
        # Queue operation for background processing
        operation = {
            "type": "CREATE",
            "session_id": session["session_id"],
            "seq_id": session.get("seq_id"),
            "version": session.get("version"),
            "data": payload.data,
            "business_context": business_context,
            "entity_context": entity_context,
            "action": "CREATE-CUSTOMER",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        
        # Queue the operation via WorkerManager
        queued_session_id = WorkerManager.queue_operation(operation)
        logger.info(f"Queued CREATE-CUSTOMER operation: session_id={queued_session_id}, phone={payload.phone}")
        
        # Log operation queued
        log_operation(
            action="CREATE-CUSTOMER",
            phone=payload.phone,
            status="QUEUED",
            session_id=session["session_id"],
            details={
                "seq_id": session.get("seq_id"),
                "version": session.get("version"),
                "queued_session_id": queued_session_id
            }
        )
        
        return SessionResponse(
            session_id=session["session_id"],
            status="QUEUED",
            message="Customer creation queued for processing"
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error queuing customer creation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Request Flow

```
HTTP Request
  │
  ├─ route_salon_request()
  │  ├─ Create session
  │  ├─ Load seq_id and version
  │  └─ Populate payload.data
  │
  ├─ create_customer()
  │  ├─ Validate input
  │  ├─ Create operation dict
  │  ├─ Queue operation via WorkerManager
  │  ├─ Log operation as QUEUED
  │  └─ Return QUEUED response
  │
  └─ HTTP Response (QUEUED)
       │
       └─ Client receives session_id immediately
            │
            └─ Can poll for result using session_id

Background Processing (Worker Thread)
  │
  ├─ OperationWorker._worker_loop()
  │  ├─ Get operation from queue
  │  ├─ Execute through DataPipeline
  │  │  ├─ Load phase
  │  │  ├─ Cache phase
  │  │  ├─ Validate phase
  │  │  ├─ Process phase
  │  │  └─ Persist phase
  │  ├─ Store result by session_id
  │  └─ Continue processing
  │
  └─ Result available via WorkerManager.get_result(session_id)
```

## Operation Lifecycle

### Step 1: Validation
```python
if not payload.phone or not payload.name or not payload.business:
    raise HTTPException(status_code=400, detail="phone, name, and business are required")
```

### Step 2: Create Operation Dict
```python
operation = {
    "type": "CREATE",
    "session_id": session["session_id"],
    "seq_id": session.get("seq_id"),
    "version": session.get("version"),
    "data": payload.data,
    "business_context": business_context,
    "entity_context": entity_context,
    "action": "CREATE-CUSTOMER",
    "timestamp": datetime.now().isoformat()
}
```

### Step 3: Queue Operation
```python
queued_session_id = WorkerManager.queue_operation(operation)
```

**What happens:**
- Operation added to worker queue
- Worker thread picks it up
- Executes through DataPipeline
- Stores result by session_id

### Step 4: Log Operation
```python
log_operation(
    action="CREATE-CUSTOMER",
    phone=payload.phone,
    status="QUEUED",
    session_id=session["session_id"],
    details={
        "seq_id": session.get("seq_id"),
        "version": session.get("version"),
        "queued_session_id": queued_session_id
    }
)
```

### Step 5: Return Response
```python
return SessionResponse(
    session_id=session["session_id"],
    status="QUEUED",
    message="Customer creation queued for processing"
)
```

## Data Passed to Worker

The operation dict contains all necessary information:

```python
{
    "type": "CREATE",                    # Operation type for routing
    "session_id": "uuid-1",              # Track this operation
    "seq_id": 1,                         # Customer seq_id
    "version": 1,                        # Version number
    "data": {                            # Request data
        "phone": "9876543210",
        "name": "John Doe",
        "business": "salon",
        "updates": {},
        "owner_name": "",
        "salon_name": "",
        "service_type": "",
        "working_hours": []
    },
    "business_context": {...},           # Context for business operations
    "entity_context": {...},             # Context for entity operations
    "action": "CREATE-CUSTOMER",         # Action name
    "timestamp": "2024-11-17T..."        # When queued
}
```

## Worker Processing

The worker thread will:

1. **Get operation from queue**
   ```python
   operation = self.operation_queue.get(timeout=1)
   ```

2. **Execute through DataPipeline**
   ```python
   result = self._process_operation(operation)
   ```

3. **Store result by session_id**
   ```python
   self.results[session_id] = result
   ```

4. **Client can retrieve result**
   ```python
   result = WorkerManager.get_result(session_id, timeout=30)
   ```

## Response Status Codes

### Immediate Response (API)
- **Status:** QUEUED
- **HTTP Code:** 200 OK
- **Message:** "Customer creation queued for processing"

### Background Processing (Worker)
- **Status:** COMPLETED or FAILED
- **Available via:** `WorkerManager.get_result(session_id)`

## Logging

### Operation Queued
```
INFO: Queued CREATE-CUSTOMER operation: session_id=uuid-1, phone=9876543210
INFO: Operation log: {
    "action": "CREATE-CUSTOMER",
    "phone": "9876543210",
    "status": "QUEUED",
    "session_id": "uuid-1",
    "timestamp": "2024-11-17T...",
    "seq_id": 1,
    "version": 1,
    "queued_session_id": "uuid-1"
}
```

### Error Handling
```
ERROR: Validation error: phone, name, and business are required
ERROR: Error queuing customer creation: [error message]
```

## Client Usage

### 1. Send Request
```bash
curl -X POST http://localhost:8000/api/v1/makerequest \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create-customer",
    "phone": "9876543210",
    "name": "John Doe",
    "business": "salon"
  }'
```

### 2. Receive Response
```json
{
    "session_id": "uuid-1",
    "status": "QUEUED",
    "message": "Customer creation queued for processing"
}
```

### 3. Poll for Result
```python
import time
from src.core.worker_manager import WorkerManager

session_id = "uuid-1"
timeout = 30
start = time.time()

while time.time() - start < timeout:
    result = WorkerManager.get_result(session_id)
    if result:
        print(f"Operation completed: {result}")
        break
    time.sleep(1)
else:
    print(f"Operation timed out after {timeout} seconds")
```

## Benefits

1. **Fast Response** - API responds immediately
2. **Scalability** - Multiple operations processed in parallel
3. **Reliability** - Operations queued and retried if needed
4. **Tracking** - Each operation has session_id for tracking
5. **Flexibility** - Client can poll or wait for result

## Concurrency

Multiple operations can be queued and processed concurrently:

```
Request 1: create_customer() → Queue operation 1 → Response (QUEUED)
Request 2: create_customer() → Queue operation 2 → Response (QUEUED)
Request 3: create_customer() → Queue operation 3 → Response (QUEUED)

Worker Thread 1: Process operation 1
Worker Thread 2: Process operation 2
Worker Thread 3: Process operation 3

All three operations processed in parallel
```

## Error Handling

### Validation Error
```python
if not payload.phone or not payload.name or not payload.business:
    raise HTTPException(status_code=400, detail="phone, name, and business are required")
```

### Queue Error
```python
except Exception as e:
    logger.error(f"Error queuing customer creation: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

## Future Enhancements

1. **Retry Logic** - Retry failed operations
2. **Priority Queue** - Process high-priority operations first
3. **Timeout Handling** - Handle long-running operations
4. **Batch Operations** - Process multiple operations in batch
5. **Webhooks** - Notify client when operation completes
6. **Status Polling** - Provide operation status endpoint

## Summary

The `create_customer` handler now queues operations for background processing instead of executing immediately. This provides:

- **Fast API Response** - Returns immediately with QUEUED status
- **Background Processing** - Worker threads handle the actual work
- **Session Tracking** - Each operation tracked by session_id
- **Result Retrieval** - Client can poll for result using session_id
- **Scalability** - Multiple operations processed in parallel
