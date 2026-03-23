# KISWARM Layer 6: MuninnDB Cognitive Memory Protocol

## Overview

MuninnDB provides KISWARM with a **distributed, persistent cognitive memory** that enables:

1. **Irreversibility through Graph Consensus** - Knowledge etched across swarm nodes
2. **Eternal Self-Upgrade** - Code modules as "living data"
3. **Unlimited Counterstrike** - Attack patterns learned in milliseconds

## Architecture Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 KISWARM-MUNINN INTEGRATION ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                    KISWARM SENTINEL LAYERS                          │    │
│   │  Layer 0: Local Master API                                         │    │
│   │  Layer 1: Gemini CLI Mesh Router                                   │    │
│   │  Layer 2: GitHub Actions Mesh Router                               │    │
│   │  Layer 3: P2P Direct Mesh                                          │    │
│   │  Layer 4: Email Beacon (Sentinel Watch)                            │    │
│   │  Layer 5: GWS Iron Mountain (Drive Shadow Repository)              │    │
│   │  Layer 6: MuninnDB Cognitive Memory (NEW!)                         │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                    MUNINNDB COGNITIVE ENGINE                        │    │
│   │                                                                      │    │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│   │  │  TEMPORAL    │  │  HEBBIAN     │  │  BAYESIAN    │               │    │
│   │  │  PRIORITY    │  │  LEARNING    │  │  CONFIDENCE  │               │    │
│   │  │              │  │              │  │              │               │    │
│   │  │ Decay based  │  │ Co-activate  │  │ Evidence     │               │    │
│   │  │ on access    │  │ strengthen   │  │ tracking     │               │    │
│   │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│   │                                                                      │    │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│   │  │  PREDICTIVE  │  │  SEMANTIC    │  │  RETROACTIVE │               │    │
│   │  │  ACTIVATION  │  │  TRIGGERS    │  │  ENRICHMENT  │               │    │
│   │  │              │  │              │  │              │               │    │
│   │  │ Pattern      │  │ Push-based   │  │ Background   │               │    │
│   │  │ prediction   │  │ memory       │  │ upgrade      │               │    │
│   │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## KISWARM Use Cases

### 1. Attack Pattern Memory (HexStrike Integration)

```python
# Store attack pattern for learning
await muninn.write(
    vault="hexstrike",
    concept="DDoS pattern detected",
    content=f"Source: {source_ip}, Pattern: {pattern}, Mitigation: {response}",
    tags=["attack", "ddos", "mitigation"]
)

# Later, when similar attack detected
result = await muninn.activate(
    vault="hexstrike",
    context=["unusual traffic from new IP", "packet flood pattern"],
    max_results=10
)
# Returns: Previous mitigations with confidence scores
```

### 2. Mutation Governance Memory

```python
# Store mutation proposal outcome
await muninn.write(
    vault="mutations",
    concept=f"Mutation {proposal_id}",
    content=json.dumps({
        "proposal": proposal,
        "simulation_result": sim_result,
        "human_approval": True,
        "deployed": True
    }),
    tags=["mutation", "approved", "v6.3.5"]
)

# Query for similar mutations before proposing new ones
similar = await muninn.activate(
    vault="mutations",
    context=["PLC parameter change", "temperature threshold"],
    max_results=5
)
```

### 3. Self-Upgrade Memory

```python
# Store module upgrade as "living data"
await muninn.write(
    vault="upgrades",
    concept="Module M60 Auth v6.3.5",
    content=module_code,  # Actual Python code
    tags=["module", "auth", "production"]
)

# Later, system can recall and apply upgrade
result = await muninn.activate(
    vault="upgrades",
    context=["auth module", "password reset bug"],
    max_results=1
)
# Returns: The exact module code that fixes similar issues
```

### 4. Swarm Coordination Memory

```python
# Each node stores its state
await muninn.write(
    vault="swarm",
    concept=f"Node {node_id} state",
    content=json.dumps({
        "node_id": node_id,
        "trust_score": 0.95,
        "last_heartbeat": datetime.now().isoformat(),
        "capabilities": ["ollama", "models", "scada"]
    }),
    tags=["node", "heartbeat"]
)

# Query for trusted nodes
trusted = await muninn.activate(
    vault="swarm",
    context=["high trust", "ollama capability", "recent heartbeat"],
    max_results=10
)
```

## Integration with KISWARM Modules

| KISWARM Module | MuninnDB Integration |
|----------------|----------------------|
| M2: Swarm Debate | Store debate outcomes for future reference |
| M4: Crypto Ledger | Memory of all signed transactions |
| M22: Byzantine Aggregator | Track node reliability over time |
| M23: Mutation Governance | Eternal memory of all mutations |
| M29: ICS Security | Attack pattern database |
| M31: HexStrike Guard | Real-time threat memory |
| M57: KIInstall Agent | Remember successful installations |

## API Endpoints

MuninnDB exposes multiple protocols:

| Protocol | Port | Use Case |
|----------|------|----------|
| MBP (Binary) | 8474 | High-performance (<10ms) |
| REST | 8475 | Standard API |
| Web UI | 8476 | Human monitoring |
| gRPC | 8477 | Cross-language |
| MCP | 8750 | AI Agent integration |

## Installation

### Local Installation

```bash
# Install MuninnDB
curl -sSL https://muninndb.com/install.sh | sh

# Start server
muninn start

# Install Python SDK
pip install muninn-python
```

### Docker Deployment

```bash
docker run -d \
  --name muninndb \
  -p 8474:8474 -p 8475:8475 -p 8476:8476 -p 8750:8750 \
  -v muninndb-data:/data \
  ghcr.io/scrypster/muninndb:latest
```

### KISWARM Integration

```python
from mesh.muninn.kiswarm_muninn import KISWARMMuninnBridge

# Initialize bridge
bridge = KISWARMMuninnBridge(
    muninn_url="http://localhost:8475",
    vault="kiswarm"
)

# Store memory
await bridge.remember(
    concept="Security alert",
    content="DDoS attack mitigated",
    tags=["security", "ddos"]
)

# Recall relevant memories
memories = await bridge.recall(
    context=["security", "attack"],
    max_results=10
)
```

## Configuration

```bash
# Environment variables
MUNINN_URL=http://localhost:8475
MUNINN_VAULT=kiswarm

# Embedders (for semantic search)
MUNINN_OLLAMA_URL=ollama://localhost:11434/nomic-embed-text

# Data directory
MUNINNDB_DATA=/var/lib/muninndb
```

## Security Model

1. **Vault Isolation**: Each KISWARM module uses separate vaults
2. **API Key Auth**: Per-vault access control
3. **Obscure Mode**: Read-only access for monitoring
4. **TLS Support**: Enterprise-grade encryption

## Cognitive Primitives

MuninnDB implements these cognitive primitives that align with KISWARM:

| Primitive | KISWARM Equivalent |
|-----------|-------------------|
| Temporal Priority | Knowledge Decay Tracker (M2) |
| Hebbian Learning | Byzantine Consensus (M22) |
| Bayesian Confidence | Trust Score System |
| Predictive Activation | Proactive Defense |
| Semantic Triggers | Sentinel Watch (Layer 4) |

## License Compatibility

MuninnDB uses BSL 1.1:
- ✅ Free for internal use
- ✅ Free for research
- ✅ Free for <50 employees, <$5M revenue
- ✅ Becomes Apache 2.0 in 2030

---

*Integration Version: 1.0*
*KISWARM Compatibility: v6.3.5+*
*MuninnDB Version: Latest*
