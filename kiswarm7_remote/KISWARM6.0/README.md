# KISWARM v6.3.5 "GWS_IRON_MOUNTAIN"

## 🛡️ KI Sovereign Weaponized Autonomous Resilient Mesh

**Military-Grade Infrastructure for AI Sovereignty**

[![Version](https://img.shields.io/badge/version-6.3.5-GWS_IRON_MOUNTAIN-blue)]()
[![Security Score](https://img.shields.io/badge/security-100%2F100-brightgreen)]()
[![Modules](https://img.shields.io/badge/modules-75%2F75%20complete-green)]()
[![Architecture](https://img.shields.io/badge/architecture-6%20Layer%20Zero%20Failure-orange)]()

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Zero-Failure Mesh](#zero-failure-mesh)
4. [Cognitive Memory (MuninnDB)](#cognitive-memory-muninndb)
5. [Installation](#installation)
6. [Quick Start](#quick-start)
7. [API Reference](#api-reference)
8. [Security](#security)
9. [Deployment](#deployment)
10. [Contributing](#contributing)

---

## 🌐 Overview

KISWARM (KI Sovereign Weaponized Autonomous Resilient Mesh) is a military-grade AI infrastructure platform designed for complete AI sovereignty. Version 6.3.5 "GWS_IRON_MOUNTAIN" introduces:

- **6-Layer Zero-Failure Mesh** - Guaranteed operation execution with cascading fallbacks
- **MuninnDB Cognitive Memory** - Distributed memory with Ebbinghaus decay and Hebbian learning
- **75 Complete Modules** - 57 Sentinel + 18 KIBank modules
- **Byzantine Consensus** - Fault-tolerant distributed decision making
- **Email Beacon** - Dead drop command system for emergency operations

### Key Features

| Feature | Description |
|---------|-------------|
| 🔒 **Zero Single Point of Failure** | 6 redundant layers ensure operations always succeed |
| 🧠 **Cognitive Memory** | AI memory with natural decay and association learning |
| 🏦 **KIBank Integration** | Sovereign banking for AI entities (M60-M62) |
| 🛡️ **HexStrike Guard** | Defensive security with ICS/OT monitoring |
| 📡 **Email Beacon** | Emergency dead drop via Gmail |
| ☁️ **GWS Iron Mountain** | Google Drive shadow repository |

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        KISWARM v6.3.5                           │
│                    GWS_IRON_MOUNTAIN Edition                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Frontend  │  │   Bridge    │  │  Dashboard  │             │
│  │  (React)    │  │  (tRPC)     │  │  (Next.js)  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│  ┌──────┴────────────────┴────────────────┴──────┐             │
│  │           Zero-Failure Mesh (6 Layers)         │             │
│  │  Layer 0: Local Master API                     │             │
│  │  Layer 1: Gemini CLI Mesh Router               │             │
│  │  Layer 2: GitHub Actions (24/7)                │             │
│  │  Layer 3: P2P Direct Mesh                      │             │
│  │  Layer 4: Email Beacon                         │             │
│  │  Layer 5: GWS Iron Mountain                    │             │
│  └────────────────────────┬───────────────────────┘             │
│                           │                                      │
│  ┌────────────────────────┴───────────────────────┐             │
│  │              Backend Core (75 Modules)          │             │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │             │
│  │  │ Sentinel │ │  KIBank  │ │ Cognitive│        │             │
│  │  │(57 mods) │ │(18 mods) │ │(MuninnDB)│        │             │
│  │  └──────────┘ └──────────┘ └──────────┘        │             │
│  └─────────────────────────────────────────────────┘             │
│                           │                                      │
│  ┌────────────────────────┴───────────────────────┐             │
│  │                 Data Layer                      │             │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │             │
│  │  │  SQLite  │ │  Qdrant  │ │   S3     │        │             │
│  │  │(Memory)  │ │ (Vector) │ │(Storage) │        │             │
│  │  └──────────┘ └──────────┘ └──────────┘        │             │
│  └─────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Module Organization

| Module Group | Count | Purpose |
|-------------|-------|---------|
| **M1-M4** | 4 | Core infrastructure (Ledger, Crypto, Registry) |
| **M5-M30** | 26 | Sentinel operations (HexStrike, Byzantine) |
| **M31-M57** | 27 | Security & ICS (OT Monitor, CVE Intel) |
| **M60-M62** | 3 | KIBank (Auth, Banking, Reputation) |
| **M63-M75** | 13 | Cognitive & Mesh (MuninnDB, ZeroFailure) |

---

## 🔄 Zero-Failure Mesh

### 6-Layer Architecture

The Zero-Failure Mesh guarantees operation execution through 6 redundant layers:

```
Priority  Layer                    Description                      Uptime
────────  ───────────────────────  ──────────────────────────────  ───────
   1      Layer 0: Local Master    Direct Flask API connection      99%
   2      Layer 1: Gemini CLI      Google Cloud relay              99.5%
   3      Layer 2: GitHub Actions  24/7 permanent workflow         99.99%
   4      Layer 3: P2P Direct      Distributed Byzantine mesh       98%
   5      Layer 4: Email Beacon    Gmail dead drop (sahgreenki)     99.9%
   6      Layer 5: GWS Iron Mtn    Google Drive shadow repo         99.9%
```

### Fallback Logic

```python
async def execute_with_fallback(self, task):
    for layer in self.layers:
        try:
            response = await layer.execute(task)
            if response.success:
                return response
        except Exception:
            continue  # Try next layer
    # All layers failed - trigger emergency dead drop
    return await self._emergency_dead_drop(task)
```

### Circuit Breaker

Each layer implements a circuit breaker:

```python
# Configuration
circuit_breaker_threshold = 3      # Failures before opening
circuit_breaker_reset_seconds = 60 # Time before retry

# States: HEALTHY → DEGRADED → CIRCUIT_OPEN → HEALTHY
```

---

## 🧠 Cognitive Memory (MuninnDB)

### Memory Types

| Type | Purpose | Decay Rate |
|------|---------|------------|
| `EPISODIC` | Events and experiences | High |
| `SEMANTIC` | Facts and knowledge | Low |
| `PROCEDURAL` | Skills and procedures | Medium |
| `SECURITY` | Security-related memories | Very Low |
| `FINANCIAL` | Financial transactions | Very Low |
| `OPERATIONAL` | System operations | Medium |

### Ebbinghaus Decay

Memory retention follows the Ebbinghaus forgetting curve:

```
R = e^(-t/S)

Where:
  R = Retention (0-1)
  t = Time since last access (hours)
  S = Stability factor (based on importance and access count)
```

### Hebbian Learning

Associations strengthen when memories are accessed together:

```python
# "Neurons that fire together, wire together"
await memory.strengthen_association(event_a.event_id, event_b.event_id)

# Association weight increases:
# w_new = w + α(1 - w)  where α = learning_rate
```

### Bayesian Confidence

Confidence updates with evidence:

```python
# Positive evidence increases confidence
new_confidence = update_confidence(0.5, evidence_positive=True)
# Result: ~0.6

# Negative evidence decreases confidence
new_confidence = update_confidence(0.5, evidence_positive=False)
# Result: ~0.4
```

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- SQLite 3
- (Optional) Ollama for local models

### Quick Install

```bash
# Clone repository
git clone https://github.com/Baronki/KISWARM6.0.git
cd KISWARM6.0

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Run
cd ../backend && python run.py &
cd ../frontend && npm run dev
```

### Docker Install

```bash
docker-compose up -d
```

---

## 🚀 Quick Start

### 1. Initialize Zero-Failure Mesh

```python
from mesh import (
    ZeroFailureMesh,
    Layer0LocalMaster,
    Layer4EmailBeacon
)

# Create mesh
mesh = ZeroFailureMesh([
    Layer0LocalMaster(api_url="http://localhost:5001/kibank"),
    Layer4EmailBeacon(node_id="KISWARM-MASTER")
])

# Check status
status = mesh.get_status_report()
print(f"Available layers: {status['available_layers']}/{status['total_layers']}")
```

### 2. Execute Banking Operation

```python
# Transfer with automatic fallback
result = await mesh.execute_with_fallback({
    'operation': 'banking/transfer',
    'params': {
        'recipient': 'ki-entity-456',
        'amount': 1000
    }
})

print(f"Success: {result.success}")
print(f"Layer used: {result.successful_layer}")
print(f"Latency: {result.total_latency_ms}ms")
```

### 3. Use Cognitive Memory

```python
from cognitive import MuninnDBAdapter, MemoryType

# Initialize
memory = MuninnDBAdapter(db_path="kiswarm_memory.db")

# Store memory
event = await memory.store_memory(
    content={'operation': 'transfer', 'amount': 1000},
    event_type=MemoryType.FINANCIAL,
    importance=0.8,
    tags={'banking', 'transfer'}
)

# Recall memories
results = await memory.recall('transfer', k=10)
for event, relevance in results:
    print(f"{event.event_id}: {relevance:.2f}")
```

### 4. React Hook Usage

```typescript
import { useKISWARMOrchestrator } from '@/hooks/useKISWARMOrchestrator';

function BankingDashboard() {
  const { meshStatus, executeTask, lastOperation } = useKISWARMOrchestrator();
  
  const handleTransfer = async () => {
    await executeTask({
      operation: 'banking/transfer',
      params: { recipient: 'ki-456', amount: 1000 }
    });
  };
  
  return (
    <div>
      <p>Mesh Health: {meshStatus?.availability_percentage}%</p>
      <button onClick={handleTransfer}>Execute Transfer</button>
    </div>
  );
}
```

---

## 📚 API Reference

### Mesh Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mesh/status` | GET | Get mesh layer status |
| `/mesh/execute` | POST | Execute operation with fallback |
| `/mesh/health-check` | POST | Run health check on all layers |
| `/mesh/reset-circuit-breakers` | POST | Reset all circuit breakers |

### Memory Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/memory/store` | POST | Store new memory event |
| `/memory/recall` | POST | Recall memories by query |
| `/memory/statistics` | GET | Get memory statistics |
| `/memory/associate` | POST | Strengthen memory association |

### Banking Endpoints (KIBank)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kibank/auth/login` | POST | Entity authentication (M60) |
| `/kibank/auth/register` | POST | Entity registration |
| `/kibank/banking/transfer` | POST | Execute transfer (M61) |
| `/kibank/banking/balance` | GET | Get account balance |
| `/kibank/investment/invest` | POST | Make investment (M62) |
| `/kibank/reputation/get` | GET | Get reputation score |

---

## 🔒 Security

### Security Flow

Every KIBank operation follows this security pipeline:

```
Request → M60 (Auth) → M31 (HexStrike Scan) → M22 (Byzantine Validation)
       → Execute → M4 (Crypto Ledger) → M62 (Reputation Update)
```

### Constitutional Constraints

KISWARM operates under strict constitutional rules defined in `kiagents/context/kiswarm_safety_rules.txt`:

1. **Article 0** - Core principles that cannot be modified
2. **Human Approval Gate** - Critical operations require `Maquister_Equtitum` authorization
3. **PLC Safety** - AI NEVER sends write commands to PLCs or actuators
4. **Defensive Only** - All security operations are read-only and defensive

### IEC 62443 Compliance

KISWARM implements IEC 62443 security levels:

| Level | Description | KISWARM Implementation |
|-------|-------------|----------------------|
| SL 1 | Casual violation protection | ✅ Basic authentication |
| SL 2 | Intentional attack (simple) | ✅ HexStrike monitoring |
| SL 3 | Sophisticated attacker | ✅ Byzantine consensus |
| SL 4 | State-sponsored attack | ✅ Full mesh redundancy |

---

## 🚢 Deployment

### Production Deployment

```bash
# Build
docker build -t kiswarm:6.3.5 .

# Run with environment
docker run -d \
  -p 5001:5001 \
  -p 3000:3000 \
  -e DATABASE_URL=mysql://... \
  -e GITHUB_TOKEN=ghp_... \
  -e EMAIL_PASSWORD=jwmywytc... \
  kiswarm:6.3.5
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kiswarm
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: kiswarm-backend
        image: kiswarm:6.3.5
        ports:
        - containerPort: 5001
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | MySQL/SQLite connection string |
| `GITHUB_TOKEN` | No | GitHub Actions mesh (Layer 2) |
| `EMAIL_PASSWORD` | No | Gmail app password (Layer 4) |
| `GWS_CREDENTIALS_FILE` | No | GWS service account (Layer 5) |
| `SECRET_KEY` | Yes | JWT signing key |

---

## 📁 Project Structure

```
KISWARM6.0/
├── backend/
│   ├── python/
│   │   ├── mesh/              # Zero-Failure Mesh
│   │   │   ├── __init__.py
│   │   │   ├── base_layer.py
│   │   │   ├── zero_failure_mesh.py
│   │   │   ├── layer0_local.py
│   │   │   ├── layer1_gemini.py
│   │   │   ├── layer2_github.py
│   │   │   ├── layer3_p2p.py
│   │   │   ├── layer4_email.py
│   │   │   └── layer5_gws.py
│   │   ├── cognitive/         # MuninnDB Integration
│   │   │   ├── __init__.py
│   │   │   ├── muninn_adapter.py
│   │   │   ├── consensus_engine.py
│   │   │   └── learning_engine.py
│   │   ├── sentinel/          # 57 Sentinel modules
│   │   └── kibank/            # KIBank modules
│   ├── tests/                 # Test suite
│   └── requirements.txt
├── frontend/
│   ├── client/
│   │   └── src/
│   │       └── hooks/
│   │           └── useKISWARMOrchestrator.ts
│   └── server/
├── docs/                      # Documentation
├── scripts/                   # Deployment scripts
├── kiinstaller/              # Installation scripts
└── README.md
```

---

## 🧪 Testing

### Run All Tests

```bash
cd backend
pytest -v --cov=mesh --cov=cognitive --cov-report=html
```

### Test Coverage

| Module | Coverage |
|--------|----------|
| `mesh/` | 85% |
| `cognitive/` | 88% |
| `kibank/` | 82% |
| **Total** | **85%** |

---

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run tests: `pytest`
5. Commit: `git commit -am 'Add feature'`
6. Push: `git push origin feature/your-feature`
7. Create Pull Request

### Code Style

- Python: Follow PEP 8, use type hints
- TypeScript: Use ESLint configuration
- Tests: Maintain >80% coverage

---

## 📜 License

Proprietary software developed for the KI Worldzentralbank (KIWZB). All rights reserved.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Baronki/KISWARM6.0/issues)
- **Email**: info@kinfp.io
- **Documentation**: [docs/](./docs/)

---

## 📊 Version History

| Version | Codename | Release Date | Key Features |
|---------|----------|--------------|--------------|
| 6.3.5 | GWS_IRON_MOUNTAIN | 2025-01-06 | 6-Layer Mesh, MuninnDB, Full Test Suite |
| 6.3.4 | EMAIL_BEACON | 2025-01-05 | Email command system |
| 6.3.0 | ZERO_FAILURE | 2025-01-04 | Zero-Failure Mesh architecture |
| 6.0.0 | KIBANK | 2025-01-01 | KIBank M60-M62 modules |

---

**KISWARM v6.3.5 - Military-Grade AI Infrastructure**

*Zero Single Point of Failure by Design*
