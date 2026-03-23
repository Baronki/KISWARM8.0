# KISWARM Zero-Failure Mesh API Documentation

## Overview

The Zero-Failure Mesh provides guaranteed operation execution through 6 redundant layers with automatic fallback cascading.

## Mesh Coordinator API

### `ZeroFailureMesh`

Main coordinator for all mesh layers.

#### Initialization

```python
from mesh import ZeroFailureMesh, MeshConfig, Layer0LocalMaster, Layer4EmailBeacon

mesh = ZeroFailureMesh(
    layers=[
        Layer0LocalMaster(api_url="http://localhost:5001"),
        Layer4EmailBeacon(node_id="KISWARM-MASTER")
    ],
    config=MeshConfig(
        max_retries_per_layer=2,
        global_timeout_seconds=120.0,
        parallel_layer_attempts=2,
        enable_emergency_dead_drop=True,
        circuit_breaker_threshold=3,
        circuit_breaker_reset_seconds=60.0
    )
)
```

#### Methods

##### `execute_with_fallback(task: Dict) -> MeshOperationResult`

Execute a task with automatic fallback through layers.

**Parameters:**
- `task` (Dict): Task definition
  - `operation` (str): Operation type (e.g., 'banking/transfer')
  - `params` (Dict): Operation parameters

**Returns:** `MeshOperationResult`
- `success` (bool): Whether operation succeeded
- `data` (Dict): Response data
- `successful_layer` (int): ID of layer that succeeded
- `attempts` (List): All layer attempts
- `total_latency_ms` (float): Total execution time
- `operation_hash` (str): SHA-256 hash for audit

**Example:**
```python
result = await mesh.execute_with_fallback({
    'operation': 'banking/transfer',
    'params': {
        'recipient': 'ki-entity-456',
        'amount': 1000
    }
})

if result.success:
    print(f"Transfer completed via Layer {result.successful_layer}")
else:
    print(f"All layers failed: {result.attempts}")
```

---

##### `execute_parallel(task: Dict) -> MeshOperationResult`

Execute task on multiple layers in parallel, return first success.

**Parameters:** Same as `execute_with_fallback`

**Use Case:** Critical operations requiring maximum reliability

**Example:**
```python
# Executes on top 2 layers simultaneously
result = await mesh.execute_parallel({
    'operation': 'banking/transfer',
    'params': {'recipient': 'ki-456', 'amount': 1000}
})
```

---

##### `broadcast(task: Dict, require_consensus: bool = False) -> MeshOperationResult`

Broadcast task to all available layers.

**Parameters:**
- `task` (Dict): Task definition
- `require_consensus` (bool): Require Byzantine consensus (default: False)
- `consensus_threshold` (float): Agreement threshold (default: 0.67)

**Example:**
```python
# Broadcast to all layers, require 67% agreement
result = await mesh.broadcast({
    'operation': 'consensus/decision',
    'params': {'proposal': 'upgrade_system'}
}, require_consensus=True)
```

---

##### `get_status_report() -> Dict`

Get comprehensive mesh status.

**Returns:**
```python
{
    'mesh_version': '6.3.5',
    'codename': 'GWS_IRON_MOUNTAIN',
    'total_layers': 6,
    'available_layers': 5,
    'availability_percentage': 83.33,
    'layers': [
        {
            'layer_id': 0,
            'name': 'Local Master API',
            'status': 'healthy',
            'is_available': True,
            'metrics': {
                'total_requests': 1000,
                'success_rate': 99.5,
                'average_latency_ms': 45.2,
                'consecutive_failures': 0
            }
        },
        # ... other layers
    ]
}
```

---

##### `health_check_all() -> Dict[int, bool]`

Run health check on all layers.

**Returns:** Dictionary mapping layer_id to health status

```python
health = await mesh.health_check_all()
# {0: True, 1: False, 2: True, 3: True, 4: True, 5: True}
```

---

## Layer API

### Base Layer Class

All layers inherit from `MeshLayer`:

```python
class MeshLayer(ABC):
    layer_id: int          # Unique identifier (0-5)
    name: str              # Human-readable name
    priority: int          # Lower = higher priority
    status: LayerStatus    # Current status
    metrics: LayerMetrics  # Performance metrics
    
    async def execute(task: Dict) -> LayerResponse
    async def health_check() -> bool
    def get_status_report() -> Dict
    async def reset_circuit_breaker() -> None
```

### LayerResponse

```python
@dataclass
class LayerResponse:
    success: bool
    data: Optional[Dict]
    error: Optional[str]
    layer_id: int
    layer_name: str
    latency_ms: float
    timestamp: datetime
    fallback_used: bool
    signature: Optional[str]
```

---

## Layer 0: Local Master API

Direct connection to KIBank Flask API.

```python
from mesh import Layer0LocalMaster

layer = Layer0LocalMaster(
    api_url="http://localhost:5001/kibank",
    timeout_seconds=10.0
)

# Supported operations
operations = {
    'auth/login': ('POST', '/auth/login'),
    'auth/register': ('POST', '/auth/register'),
    'banking/transfer': ('POST', '/banking/transfer'),
    'banking/balance': ('GET', '/banking/balance'),
    'investment/invest': ('POST', '/investment/invest'),
    'reputation/get': ('GET', '/reputation/get')
}
```

---

## Layer 4: Email Beacon

Emergency communication via Gmail dead drop.

```python
from mesh import Layer4EmailBeacon, EmailConfig

layer = Layer4EmailBeacon(
    config=EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        imap_host="imap.gmail.com",
        imap_port=993,
        username="sahgreenki@gmail.com",
        password="YOUR_APP_PASSWORD_HERE"  # App password
    ),
    node_id="KISWARM-MASTER",
    authorized_senders=["admin@example.com"]
)

# Operations
# 1. send_alert - Emergency dead drop
# 2. send_command - Send command to other nodes
# 3. check_commands - Check for pending commands
```

### Command Format

**Subject Line:**
```
[KISWARM-CMD] {NODE_ID}: {COMMAND}
```

**Supported Commands:**
- `ALL: REPORT STATUS` - All nodes report status
- `{NODE}: RESTART TUNNEL` - Restart specific node's tunnel
- `ALL: DEPLOY MODELS` - Deploy KI models
- `ALL: DISCOVER NODES` - Announce nodes

---

## Layer 5: GWS Iron Mountain

Google Drive shadow repository.

```python
from mesh import Layer5GWSIronMountain

layer = Layer5GWSIronMountain(
    credentials_file="/path/to/service-account.json",
    drive_folder="KISWARM_IRON_MOUNTAIN",
    cache_dir="/tmp/kiswarm_cache"
)

# Operations
# 1. download - Download file from Drive
# 2. upload - Upload file to Drive
# 3. list - List files in Iron Mountain
# 4. search - Search for files
# 5. sync_repo - Sync entire repository
```

---

## Circuit Breaker Pattern

Each layer implements a circuit breaker:

```python
# Configuration
layer.circuit_breaker_threshold = 3      # Failures before opening
layer.circuit_breaker_reset_seconds = 60  # Time before retry

# States
class LayerStatus(Enum):
    HEALTHY = "healthy"          # Normal operation
    DEGRADED = "degraded"        # Some failures
    UNHEALTHY = "unhealthy"      # Multiple failures
    OFFLINE = "offline"          # Not responding
    CIRCUIT_OPEN = "circuit_open"  # Circuit breaker triggered
```

---

## Error Handling

### Custom Exceptions

```python
from mesh.exceptions import (
    MeshLayerError,
    CircuitBreakerOpen,
    AllLayersFailed,
    ConsensusFailed,
    OperationTimeout
)

try:
    result = await mesh.execute_with_fallback(task)
except AllLayersFailed as e:
    print(f"All {len(e.attempts)} layers failed")
except OperationTimeout as e:
    print(f"Operation timed out after {e.timeout_seconds}s")
```

---

## Best Practices

### 1. Always Check Results

```python
result = await mesh.execute_with_fallback(task)

if not result.success:
    logger.error(f"Operation failed: {result.attempts}")
    # Handle failure or trigger manual intervention
```

### 2. Use Parallel Execution for Critical Operations

```python
# For high-value transfers
if amount > 10000:
    result = await mesh.execute_parallel(task)
```

### 3. Monitor Mesh Health

```python
# Schedule regular health checks
async def monitor_mesh():
    while True:
        health = await mesh.health_check_all()
        unavailable = [k for k, v in health.items() if not v]
        if unavailable:
            alert(f"Layers offline: {unavailable}")
        await asyncio.sleep(60)
```

### 4. Reset Circuit Breakers After Manual Fix

```python
# After fixing underlying issue
await mesh.reset_all_circuit_breakers()
```

---

## TypeScript/React Integration

```typescript
import { useKISWARMOrchestrator } from '@/hooks/useKISWARMOrchestrator';

function MyComponent() {
  const { 
    meshStatus, 
    executeTask, 
    lastOperation,
    isExecuting 
  } = useKISWARMOrchestrator();
  
  const handleTransfer = async () => {
    const result = await executeTask({
      operation: 'banking/transfer',
      params: { recipient: 'ki-456', amount: 1000 }
    });
    
    if (result.success) {
      toast.success(`Transfer completed via Layer ${result.successful_layer}`);
    }
  };
  
  return (
    <div>
      <p>Mesh Health: {meshStatus?.availability_percentage}%</p>
      <button onClick={handleTransfer} disabled={isExecuting}>
        {isExecuting ? 'Executing...' : 'Transfer'}
      </button>
    </div>
  );
}
```
