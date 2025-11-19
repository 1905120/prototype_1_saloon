# Response Pool Pattern - Wait for Worker Results

## Overview

Updated the API handler to use a response pool pattern. The handler queues an operation and then waits for the result from the worker thread using `WorkerManager.get_result()` with a timeout. This allows the API to:

1. Queue operation for background processing
2. Wait for worker thread to complete
3. Retrieve result from response pool
4. Return result to client
5. Support parallel requests independently

## Architecture

```
API Handler (Request 1)
  │
  ├─ Queue operation 1
  │
  ├─ Wait for result (timeout=30s)
  │  └─ Blocks until result available
  │
  └─ Return response

API Handler (Request 2) [PARALLEL]
  │
  ├─ Queue operation 2
  │
  ├─ Wait for result (timeout=30s)
  │  └─ Blocks until result available
  │
  └─ Return response

Worker Thread 1
  ├─ Process operation 1
  ├─ Store result in response pool
  └─ Continue

Worker Thread 2
  ├─ Process operation 2
  ├─ Store result in response pool
  └─ Continue
```

## Implementation

### Handler Flow

```python
async def create_customer(payload, background_tasks, business_context, entity_context, session):
    # Step 1: Validate
    if not payload.phone or not payload.name or not payload.business:
        raise HTTPException(status_code=400, detail="...")
    
    try:
        # Step 2: Create operation
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
        
        # Step 3: Queue operation
        queued_session_id = WorkerManager.queue_operation(operation)
        logger.info(f"Queued CREATE-CUSTOMER operation: session_id={queued_session_id}")
        
        # Step 4: Wait for result from response pool
        result = WorkerManager.get_result(session["session_id"], timeout=30)
        
        # Step 5: Check if result available
        if result is None:
            logger.error(f"Operation timed out for session: {session['session_id']}")
            raise HTTPException(status_code=504, detail="Operation timed out")
        
        # Step 6: Check if operation failed
        if result.get("status") == "FAILED":
            logger.error(f"Operation failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=f"Operation failed: {result.get('error')}")
        
        # Step 7: Log completion
        log_operation(
            action="CREATE-CUSTOMER",
            phone=payload.phone,
            status="COMPLETED",
            session_id=session["session_id"],
            details={...}
        )
        
        # Step 8: Return response
        return SessionResponse(
            session_id=session["session_id"],
            status="COMPLETED",
            message="Customer creation completed"
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Request/Response Flow

```
Client Request
  │
  ├─ HTTP POST /api/v1/makerequest
  │  └─ {action: "create-customer", phone: "...", name: "...", business: "salon"}
  │
  ├─ route_salon_request()
  │  ├─ Create session
  │  ├─ Load seq_id and version
  │  └─ Call create_customer()
  │
  ├─ create_customer()
  │  ├─ Validate input
  │  ├─ Create operation dict
  │  ├─ Queue operation via WorkerManager
  │  │  └─ Operation added to queue
  │  │
  │  ├─ Wait for result (BLOCKING)
  │  │  └─ WorkerManager.get_result(session_id, timeout=30)
  │  │     └─ Polls response pool every 100ms
  │  │
  │  ├─ Worker thread processes operation
  │  │  ├─ Execute through DataPipeline
  │  │  ├─ Store result in response pool
  │  │  └─ Result available
  │  │
  │  ├─ Handler receives result
  │  ├─ Check status (COMPLETED or FAILED)
  │  ├─ Log operation
  │  └─ Return response
  │
  └─ HTTP Response
     └─ {session_id: "...", status: "COMPLETED", message: "..."}
```

## Response Pool Mechanism

### WorkerManager.get_result()

```python
@staticmethod
def get_result(session_id: str, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """
    Get operation result by session ID
    
    Args:
        session_id: Session identifier
        timeout: Wait timeout in seconds
    
    Returns:
        Operation result or None if not ready
    """
    # Wait for result if timeout specified
    if timeout:
        import time
        start = time.time()
        while time.time() - start < timeout:
            if session_id in self.results:
                return self.results.pop(session_id)
            time.sleep(0.1)
        return None
    
    return self.results.pop(session_id, None)
```

### Response Pool Storage

```python
# In OperationWorker
self.results = {}  # Dictionary storing results by session_id

# When operation completes
self.results[session_id] = {
    "status": "COMPLETED",
    "session_id": session_id,
    "operation_type": "CREATE",
    "session": {...}
}

# Handler retrieves
result = self.results.pop(session_id)  # Remove and return
```

## Timeout Handling

### Timeout Scenarios

**Scenario 1: Result Available Before Timeout**
```
T0: Handler calls get_result(timeout=30)
T1: Worker processes operation
T2: Result stored in pool
T3: Handler retrieves result (T3 < T0+30)
T4: Handler returns response
```

**Scenario 2: Timeout Exceeded**
```
T0: Handler calls get_result(timeout=30)
T1: Worker processing...
T2: Worker processing...
...
T30: Timeout reached
T31: Handler raises HTTPException(504, "Operation timed out")
```

### Timeout Configuration

```python
# Current: 30 second timeout
result = WorkerManager.get_result(session["session_id"], timeout=30)

# Can be adjusted based on operation complexity
result = WorkerManager.get_result(session["session_id"], timeout=60)  # 60 seconds
```

## Error Handling

### Timeout Error
```python
if result is None:
    logger.error(f"Operation timed out for session: {session['session_id']}")
    raise HTTPException(status_code=504, detail="Operation timed out")
```

**HTTP Status:** 504 Gateway Timeout

### Operation Failed
```python
if result.get("status") == "FAILED":
    logger.error(f"Operation failed: {result.get('error')}")
    raise HTTPException(status_code=500, detail=f"Operation failed: {result.get('error')}")
```

**HTTP Status:** 500 Internal Server Error

### Validation Error
```python
if not payload.phone or not payload.name or not payload.business:
    raise HTTPException(status_code=400, detail="phone, name, and business are required")
```

**HTTP Status:** 400 Bad Request

## Parallel Request Handling

### Multiple Concurrent Requests

```
Request 1 (Phone: 111)
  ├─ Queue operation 1
  ├─ Wait for result (timeout=30)
  └─ Return response

Request 2 (Phone: 222) [CONCURRENT]
  ├─ Queue operation 2
  ├─ Wait for result (timeout=30)
  └─ Return response

Request 3 (Phone: 333) [CONCURRENT]
  ├─ Queue operation 3
  ├─ Wait for result (timeout=30)
  └─ Return response

Worker Thread 1: Process operation 1
Worker Thread 2: Process operation 2
Worker Thread 3: Process operation 3

All three requests handled independently and concurrently
```

### Key Points

1. **Independent Waiting** - Each request waits for its own result
2. **Parallel Processing** - Multiple operations processed simultaneously
3. **No Blocking** - Other requests not blocked by one request's wait
4. **Timeout Per Request** - Each request has its own timeout

## Response Structure

### Successful Response

```python
{
    "status": "COMPLETED",
    "session_id": "uuid-1",
    "operation_type": "CREATE",
    "session": {
        "session_id": "uuid-1",
        "phone": "9876543210",
        "operation_type": "CREATE",
        "status": "PERSISTED",
        "seq_id": 1,
        "version": 1,
        "phases": {
            "load": {...},
            "cache": {...},
            "validate": {...},
            "process": {...},
            "persist": {...}
        }
    }
}
```

### Failed Response

```python
{
    "status": "FAILED",
    "error": "Error message describing what went wrong",
    "session_id": "uuid-1"
}
```

## Logging

### Operation Queued
```
INFO: Queued CREATE-CUSTOMER operation: session_id=uuid-1, phone=9876543210
```

### Waiting for Result
```
DEBUG: Waiting for result with timeout=30 seconds
DEBUG: Polling response pool...
```

### Result Received
```
INFO: Retrieved result for session: uuid-1
INFO: Operation log: {
    "action": "CREATE-CUSTOMER",
    "phone": "9876543210",
    "status": "COMPLETED",
    "session_id": "uuid-1",
    "timestamp": "2024-11-17T...",
    "seq_id": 1,
    "version": 1,
    "result": {...}
}
```

### Timeout
```
ERROR: Operation timed out for session: uuid-1
```

### Failure
```
ERROR: Operation failed for session: uuid-1, error: [error message]
```

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Queue Time | <1ms | Operation added to queue |
| Wait Time | Variable | Depends on operation complexity |
| Poll Interval | 100ms | Check response pool every 100ms |
| Timeout | 30s | Default timeout for operation |
| Concurrent Requests | Unlimited | Each request independent |

## Benefits

1. **Synchronous API** - Client gets response when operation completes
2. **Parallel Processing** - Multiple operations processed simultaneously
3. **Independent Requests** - Each request waits for its own result
4. **Timeout Protection** - Prevents indefinite waiting
5. **Error Handling** - Clear error responses for failures
6. **Scalability** - Handles many concurrent requests

## Comparison

### Before (Immediate Queue)
```
Handler queues operation → Returns QUEUED immediately
Client must poll for result
```

### After (Wait for Result)
```
Handler queues operation → Waits for result → Returns COMPLETED
Client gets result immediately
```

## Future Enhancements

1. **Configurable Timeout** - Allow per-operation timeout
2. **Retry Logic** - Retry failed operations
3. **Priority Queue** - Process high-priority operations first
4. **Batch Operations** - Process multiple operations together
5. **Webhooks** - Notify client via webhook when complete
6. **Long Polling** - Support long polling for result
7. **WebSocket** - Real-time result updates via WebSocket

## Summary

The response pool pattern allows the API handler to:

1. Queue operation for background processing
2. Wait for worker thread to complete (with timeout)
3. Retrieve result from response pool
4. Return result to client
5. Support parallel requests independently

This provides a synchronous API experience while leveraging background processing for scalability.
