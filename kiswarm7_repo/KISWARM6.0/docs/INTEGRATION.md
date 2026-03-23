# KISWARM v6.0 Integration Guide

## Overview

This guide explains how to set up and integrate the KISWARM v6.0 platform, combining KISWARM5.0 backend with kinfp-portal frontend and the new KIBank modules.

## Prerequisites

### System Requirements
- Python 3.10+
- Node.js 18+
- pnpm 8+
- 8GB+ RAM
- 20GB+ disk space

### External Services
- Ollama (LLM runtime)
- Qdrant (vector database) - optional

## Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd KISWARM6.0/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start backend server
python run.py
# Backend runs on http://localhost:11436
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd KISWARM6.0/frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
# Frontend runs on http://localhost:3000
```

### 3. Bridge Setup

```bash
# Navigate to bridge directory
cd KISWARM6.0/bridge

# Install dependencies
pnpm install

# Start bridge server
pnpm dev
# Bridge runs on http://localhost:3001
```

## Integration Points

### 1. KISWARM5.0 Sentinel Integration

The KISWARM5.0 backend modules are integrated without modification:

```python
# In backend/run.py

# Import sentinel modules conditionally
try:
    from sentinel.sentinel_api import app as sentinel_app
    SENTINEL_AVAILABLE = True
except ImportError as e:
    SENTINEL_AVAILABLE = False
```

All 57 modules and 360+ endpoints are available:
- `/sentinel/extract` - Knowledge extraction
- `/sentinel/debate` - Swarm debate
- `/firewall/scan` - Security scanning
- `/ledger/*` - Cryptographic ledger
- `/hexstrike/*` - Security guard
- `/solar-chase/*` - Planetary machine

### 2. KIBank Module Integration

The new KIBank modules are integrated as Flask blueprints:

```python
# In backend/run.py

from kibank.m60_auth import KIBankAuthModule
from kibank.m61_banking import KIBankBankingModule
from kibank.m62_investment import KIBankInvestmentModule

# Initialize modules
_auth = KIBankAuthModule()
_banking = KIBankBankingModule()
_investment = KIBankInvestmentModule()
```

### 3. tRPC Bridge Integration

The bridge connects Flask to the React frontend:

```typescript
// In bridge/trpc-bridge.ts

class FlaskAPIClient {
  async get<T>(path: string, params?: Record<string, unknown>): Promise<T> {
    const response = await this.client.get<T>(path, { params });
    return response.data;
  }
  
  async post<T>(path: string, data?: Record<string, unknown>): Promise<T> {
    const response = await this.client.post<T>(path, data);
    return response.data;
  }
}
```

## Security Flow Integration

Every transaction goes through the complete security pipeline:

### Step 1: Authentication (M60)

```python
# Validate session
session = _auth.get_session(session_id)
if not session or session["status"] != "active":
    return {"error": "Unauthorized"}, 401
```

### Step 2: HexStrike Security Scan (M31)

```python
# Scan for threats
from sentinel.hexstrike_guard import HexStrikeGuard
guard = HexStrikeGuard()
scan_result = guard.scan_transfer(transfer_data)
if scan_result.blocked:
    return {"error": "Security threat detected"}, 403
```

### Step 3: Byzantine Validation (M22)

```python
# Validate with Byzantine consensus
from sentinel.byzantine_aggregator import ByzantineFederatedAggregator
aggregator = ByzantineFederatedAggregator()
validation = aggregator.validate_transfer(transfer_data)
if not validation.valid:
    return {"error": "Validation failed"}, 400
```

### Step 4: Cryptographic Ledger (M4)

```python
# Sign and record in ledger
from sentinel.crypto_ledger import CryptographicKnowledgeLedger
ledger = CryptographicKnowledgeLedger()
entry = ledger.append(transfer_record)
```

### Step 5: Reputation Update (M62)

```python
# Update user reputation
_investment.update_reputation(
    user_id=user_id,
    event_type=ReputationEventType.TRANSACTION_SUCCESS,
    reference=transfer_id,
)
```

## API Endpoints

### KISWARM5.0 Endpoints (Preserved)

All 360+ endpoints from KISWARM5.0 remain unchanged:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health |
| `/sentinel/extract` | POST | Knowledge extraction |
| `/sentinel/debate` | POST | Swarm debate |
| `/sentinel/search` | GET | Search memory |
| `/firewall/scan` | POST | Security scan |
| `/ledger/status` | GET | Ledger state |
| `/ledger/verify` | GET | Integrity check |
| `/hexstrike/status` | GET | Guard status |
| `/solar-chase/status` | GET | Solar chase |

### KIBank Endpoints (New)

24 new endpoints across 3 modules:

#### M60: Authentication (8 endpoints)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kibank/auth/oauth/login` | POST | Start OAuth flow |
| `/kibank/auth/oauth/callback` | POST | Handle OAuth callback |
| `/kibank/auth/ki-entity/register` | POST | Register KI-Entity |
| `/kibank/auth/ki-entity/verify` | POST | Verify KI-Entity |
| `/kibank/auth/session` | GET | Get session |
| `/kibank/auth/logout` | POST | Logout |
| `/kibank/auth/permissions` | GET | Get permissions |
| `/kibank/auth/refresh-token` | POST | Refresh token |

#### M61: Banking (8 endpoints)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kibank/accounts/create` | POST | Create account |
| `/kibank/accounts/list` | GET | List accounts |
| `/kibank/accounts/:id` | GET | Get account |
| `/kibank/transfers/internal` | POST | Internal transfer |
| `/kibank/transfers/sepa` | POST | SEPA transfer |
| `/kibank/transfers/history` | GET | Transaction history |
| `/kibank/transfers/validate` | POST | Validate transfer |
| `/kibank/transfers/:id/status` | GET | Transfer status |

#### M62: Investment (8 endpoints)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kibank/portfolio/:userId` | GET | Get portfolio |
| `/kibank/portfolio/invest` | POST | Make investment |
| `/kibank/reputation/:userId` | GET | Get reputation |
| `/kibank/reputation/update` | POST | Update reputation |
| `/kibank/trading-limits/:userId` | GET | Get limits |
| `/kibank/trading-limits/request` | POST | Request increase |
| `/kibank/investments/history` | GET | Investment history |
| `/kibank/investments/divest` | POST | Divest holding |

## Frontend Integration

### Using tRPC Procedures

```typescript
// In React component
import { trpc } from '@/lib/trpc';

function BankingPage() {
  // Query accounts
  const { data: accounts } = trpc.kibankBanking.listAccounts.useQuery();
  
  // Execute transfer
  const transfer = trpc.kibankBanking.internalTransfer.useMutation();
  
  const handleTransfer = () => {
    transfer.mutate({
      fromAccount: 'ACC-123',
      toAccount: 'ACC-456',
      amount: 100.00,
      currency: 'EUR',
      reference: 'REF-001',
    });
  };
  
  return (
    // UI components
  );
}
```

### Type Safety

All procedures are fully typed:

```typescript
// Types are automatically inferred
type AccountsResponse = Awaited<ReturnType<typeof trpc.kibankBanking.listAccounts.query>>;
type TransferInput = Parameters<typeof trpc.kibankBanking.internalTransfer.mutate>[0];
```

## Testing

### Backend Tests

```bash
# Run Python tests
cd backend
pytest tests/

# Run specific module tests
pytest tests/test_m60_auth.py
pytest tests/test_m61_banking.py
pytest tests/test_m62_investment.py
```

### Frontend Tests

```bash
# Run frontend tests
cd frontend
pnpm test
```

### Integration Tests

```bash
# Run integration tests
cd bridge
pnpm test
```

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:11436/health

# Comprehensive check
curl http://localhost:11436/health/check-all
```

### Metrics

```bash
# Auth module stats
curl http://localhost:11436/kibank/auth/stats

# Banking module stats
curl http://localhost:11436/kibank/banking/stats

# Investment module stats
curl http://localhost:11436/kibank/investment/stats
```

## Troubleshooting

### Common Issues

1. **Sentinel modules not loading**
   ```
   Solution: Ensure KISWARM5.0 is cloned in the repos directory
   ```

2. **tRPC connection refused**
   ```
   Solution: Verify Flask backend is running on port 11436
   ```

3. **Authentication failures**
   ```
   Solution: Check session token and permissions
   ```

4. **CORS errors**
   ```
   Solution: Verify CORS configuration in Flask app
   ```

### Logs

```bash
# Backend logs
tail -f ~/logs/kiswarm6_api.log

# Frontend logs
# Check browser console

# Bridge logs
# Check terminal output
```

## Production Deployment

### Environment Variables

```bash
# Backend
export FLASK_ENV=production
export KISWARM_HOME=/opt/kiswarm

# Frontend
export VITE_API_URL=https://api.kiswarm.io

# Bridge
export FLASK_API_URL=https://api.kiswarm.io
```

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 11436
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:11436", "run:app"]
```

### Kubernetes

```yaml
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kiswarm6-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kiswarm6-backend
  template:
    spec:
      containers:
      - name: backend
        image: kiswarm6-backend:latest
        ports:
        - containerPort: 11436
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/Baronki2/KISWARM/issues
- Documentation: https://docs.kiswarm.io
