# API Flow - Unified Request Routing

## Architecture

All requests go through a single entry point `/api/v1/makerequest` which parses the JSON and routes to the appropriate v1 endpoint handler.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT REQUEST                                │
│              POST /api/v1/makerequest                            │
│                                                                   │
│  {                                                               │
│    "action": "create-customer",                                 │
│    "phone": "9876543210",                                       │
│    "name": "John Doe"                                           │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              MAIN ENDPOINT (main.py)                             │
│           /api/v1/makerequest                                   │
│                                                                   │
│  1. Parse JSON payload                                          │
│  2. Extract action field                                        │
│  3. Validate action                                             │
│  4. Route to appropriate v1 handler                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
        ┌──────────────────┐  ┌──────────────────┐
        │ create-customer  │  │ update-customer  │
        │ delete-customer  │  │ create-client    │
        │ update-client    │  │ delete-client    │
        └──────────────────┘  └──────────────────┘
                    ↓                   ↓
┌─────────────────────────────────────────────────────────────────┐
│         V1 ENDPOINT HANDLERS (v1versionapi.py)                  │
│                                                                   │
│  - create_customer()                                            │
│  - update_customer()                                            │
│  - delete_customer()                                            │
│  - create_client()                                              │
│  - update_client()                                              │
│  - delete_client()                                              │
│  - get_session()                                                │
│                                                                   │
│  Each handler:                                                  │
│  1. Validates input                                             │
│  2. Calls app_context method                                    │
│  3. Creates queue item                                          │
│  4. Enqueues for processing                                     │
│  5. Adds background task                                        │
│  6. Returns session_id                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         BACKGROUND PROCESSING                                    │
│                                                                   │
│  process_queue_item():                                          │
│  1. Execute pipeline (Load → Cache → Validate → Process → Persist)
│  2. Update session with results                                 │
│  3. Handle errors                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         RESPONSE TO CLIENT                                       │
│                                                                   │
│  {                                                               │
│    "session_id": "uuid-xxx",                                    │
│    "status": "QUEUED",                                          │
│    "message": "Request queued for processing..."                │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         CLIENT POLLS FOR RESULTS                                 │
│                                                                   │
│  GET /v1/session/{session_id}                                   │
│                                                                   │
│  Returns complete session with all phases                       │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Single Entry Point
```
POST /api/v1/makerequest
Content-Type: application/json

{
  "action": "create-customer",
  "phone": "9876543210",
  "name": "John Doe"
}
```

### 2. Main Endpoint Processing
- Parses the JSON payload
- Extracts the `action` field
- Validates action against allowed actions
- Routes to appropriate v1 handler function

### 3. V1 Handler Processing
- Validates required fields
- Calls ApplicationContext method
- Creates queue item
- Enqueues for background processing
- Returns session_id immediately

### 4. Background Processing
- Pipeline executes: Load → Cache → Validate → Process → Persist
- Updates session with results
- Handles errors gracefully

### 5. Client Polls for Results
```
GET /v1/session/{session_id}

Response:
{
  "session_id": "uuid-xxx",
  "phone": "9876543210",
  "status": "PERSISTED",
  "seq_id": 1,
  "version": 1,
  "data": {...},
  "phases": {
    "load": {...},
    "cache": {...},
    "validate": {...},
    "process": {...},
    "persist": {...}
  },
  "errors": []
}
```

## Supported Actions

| Action | Handler | Description |
|--------|---------|-------------|
| `create-customer` | `create_customer()` | Create new customer |
| `update-customer` | `update_customer()` | Update existing customer |
| `delete-customer` | `delete_customer()` | Delete customer (soft delete) |
| `create-client` | `create_client()` | Create new salon/client |
| `update-client` | `update_client()` | Update existing client |
| `delete-client` | `delete_client()` | Delete client (soft delete) |

## Benefits

✅ **Single Entry Point** - All requests through `/api/v1/makerequest`
✅ **Clean Routing** - JSON action field determines handler
✅ **Async Processing** - Non-blocking, background execution
✅ **Session Tracking** - Poll for results anytime
✅ **Error Handling** - Comprehensive error responses
✅ **Modular** - Handlers in separate file for maintainability

## Code Structure

```
src/
├── main.py                 # Main entry point, /api/v1/makerequest
├── v1versionapi.py        # V1 endpoint handlers
├── core/
│   ├── context.py         # ApplicationContext
│   ├── pipeline.py        # 5-phase pipeline
│   ├── session.py         # Session management
│   ├── queue_manager.py   # Request queue
│   └── ...
└── ...
```

## Example Usage

### Create Customer
```bash
curl -X POST http://localhost:8000/api/v1/makerequest \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create-customer",
    "phone": "9876543210",
    "name": "John Doe"
  }'
```

### Poll for Results
```bash
curl http://localhost:8000/v1/session/550e8400-e29b-41d4-a716-446655440000
```

### Update Customer
```bash
curl -X POST http://localhost:8000/api/v1/makerequest \
  -H "Content-Type: application/json" \
  -d '{
    "action": "update-customer",
    "phone": "9876543210",
    "updates": {
      "name": "Jane Doe"
    }
  }'
```
