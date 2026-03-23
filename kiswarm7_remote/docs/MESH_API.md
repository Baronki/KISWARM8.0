# KISWARM 6-Layer Zero-Failure Mesh API

## Overview

The Zero-Failure Mesh provides military-grade reliability through a 6-layer failover architecture. Each layer operates independently with circuit breaker protection, ensuring no single point of failure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   ZERO-FAILURE MESH v6.3.5                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 0: Local Master API (Priority 1)                        │
│  ├── Direct Flask connection to localhost:5000                  │
│  ├── Latency: <10ms                                             │
│  ├── Reliability: 99.9% (local)                                 │
│  └── Status: PRIMARY                                            │
│                                                                 │
│  LAYER 1: Gemini CLI Router (Priority 2)                        │
│  ├── Google Cloud relay via Gemini CLI                          │
│  ├── Latency: 100-500ms                                         │
│  ├── Reliability: 99.5%                                         │
│  └── Status: FAILOVER                                           │
│                                                                 │
│  LAYER 2: GitHub Actions (Priority 3)                           │
│  ├── 24/7 permanent runner                                      │
│  ├── Latency: 1-5s                                              │
│  ├── Reliability: 99.99%                                        │
│  └── Status: PERMANENT                                          │
│                                                                 │
│  LAYER 3: P2P Direct Mesh (Priority 4)                          │
│  ├── Byzantine consensus with peer nodes                         │
│  ├── Latency: Variable                                          │
│  ├── Reliability: 95%+                                          │
│  └── Status: DISTRIBUTED                                        │
│                                                                 │
│  LAYER 4: Email Beacon (Priority 5)                             │
│  ├── Emergency dead drop via SMTP                               │
│  ├── Latency: 1-60s                                             │
│  ├── Reliability: 99.99%                                        │
│  └── Status: EMERGENCY                                          │
│                                                                 │
│  LAYER 5: GWS Iron Mountain (Priority 6)                        │
│  ├── Google Drive shadow storage                                │
│  ├── Latency: 5-30s                                             │
│  ├── Reliability: 99.99%                                        │
│  └── Status: SHADOW                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```python
from mesh import ZeroFailureMesh, Layer0LocalMaster, Layer4EmailBeacon

# Initialize mesh
mesh = ZeroFailureMesh()

# Register layers
mesh.register_layer(Layer0LocalMaster(base_url="http://localhost:5000"))
mesh.register_layer(Layer4EmailBeacon(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your_email@gmail.com",
    smtp_password="your_app_password",
    beacon_address="beacon@kiswarm.io"
))

# Initialize all layers
await mesh.initialize()

# Execute request with automatic failover
async def my_request():
    return {"operation": "status_check"}

result = await mesh.execute(my_request)
print(result)
```

## Circuit Breaker Pattern

Each layer implements the circuit breaker pattern with three states:

### States

1. **CLOSED**: Normal operation, requests pass through
2. **OPEN**: Failing, requests are rejected immediately
3. **HALF_OPEN**: Testing recovery, limited requests allowed

### Configuration

```python
from mesh.base_layer import LayerConfig

config = LayerConfig(
    name="local_master",
    priority=0,               # Lower = higher priority
    timeout_ms=10000,         # Request timeout
    failure_threshold=5,      # Failures before opening circuit
    recovery_timeout_ms=30000, # Time before attempting recovery
    half_open_max_calls=3,    # Test calls in half-open state
    enabled=True              # Layer enabled/disabled
)
```

## Layer Implementations

### Layer 0: Local Master API

```python
from mesh.layer0_local import Layer0LocalMaster

layer = Layer0LocalMaster(
    base_url="http://localhost:5000"
)

# Check health
is_healthy = await layer.health_check()

# Execute request
result = await layer.execute(
    lambda: None,
    endpoint="/api/v1/status",
    method="GET"
)
```

### Layer 4: Email Beacon

```python
from mesh.layer4_email import Layer4EmailBeacon

layer = Layer4EmailBeacon(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="sender@gmail.com",
    smtp_password="app_password",
    beacon_address="recipient@kiswarm.io",
    sender_name="KISWARM-Mesh"
)

# Send emergency request
result = await layer.execute(
    lambda: None,
    operation="emergency_status",
    payload={"system": "critical"}
)

# Send alert (non-mesh)
await layer.send_alert(
    subject="System Alert",
    message="Critical threshold exceeded",
    priority="HIGH"
)
```

## Byzantine Consensus

For critical operations requiring multi-layer agreement:

```python
# Execute with consensus (requires 2+ layers to agree)
result = await mesh.execute_with_consensus(
    my_critical_request,
    min_agreements=2
)
```

## Monitoring

```python
# Get mesh status
status = mesh.get_status()

print(f"Total layers: {status['total_layers']}")
print(f"Available: {status['available_layers']}")

for layer_status in status['layers']:
    print(f"{layer_status['name']}: {layer_status['state']}")
    print(f"  Success rate: {layer_status['metrics']['success_rate']}%")
```

## Error Handling

```python
from mesh import (
    MeshExhaustedError,
    InsufficientLayersError,
    ConsensusError,
    LayerUnavailableError,
    LayerTimeoutError
)

try:
    result = await mesh.execute(my_request)
except MeshExhaustedError:
    print("All layers failed after retries")
except LayerTimeoutError:
    print("Layer timed out")
except LayerUnavailableError:
    print("Layer not available")
```

## Best Practices

1. **Layer Priority**: Lower priority number = higher priority
2. **Timeouts**: Set appropriate timeouts for each layer type
3. **Recovery**: Configure recovery timeout based on expected recovery time
4. **Consensus**: Use consensus for critical operations only
5. **Monitoring**: Check mesh status regularly

## API Reference

### ZeroFailureMesh

| Method | Description |
|--------|-------------|
| `register_layer(layer)` | Register a layer with the mesh |
| `initialize()` | Initialize all layers |
| `execute(request)` | Execute with automatic failover |
| `execute_with_consensus(request, min_agreements)` | Execute with Byzantine consensus |
| `get_status()` | Get mesh status |
| `shutdown()` | Gracefully shutdown mesh |

### BaseLayer

| Method | Description |
|--------|-------------|
| `execute(request)` | Execute request through layer |
| `is_available` | Check if layer is available |
| `get_status()` | Get layer status |
| `reset()` | Reset layer to initial state |

## Credentials

| Service | Usage |
|---------|-------|
| Email Beacon | `sahgreenki@gmail.com` (SMTP) |
| GitHub Token | Required for Layer 2 (GitHub Actions) |
| Google Drive | Required for Layer 5 (GWS Iron Mountain) |
