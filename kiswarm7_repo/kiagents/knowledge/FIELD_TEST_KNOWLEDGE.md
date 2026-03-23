# KISWARM SCADA v6.3.0 - Field Test Knowledge Base

## Purpose
This knowledge base captures all lessons learned from Field Test #2 for the KIInstaller to use during future deployments.

---

## Critical Lessons Learned

### 1. Python Path Configuration (CRITICAL)

**Problem**: Module import errors and IndentationError in `__init__.py`

**Solution**:
```bash
# PYTHONPATH must include BOTH directories
export PYTHONPATH="${PYTHONPATH}:/path/to/backend:/path/to/backend/python"
```

**Why**: KIBank modules are in `backend/python/kibank` but need access to `sentinel` modules in `backend/python/sentinel`. Without both paths, imports fail.

### 2. KIBank `__init__.py` Import Structure

**Problem**: IndentationError when importing all modules at once

**Solution**: Use minimal, sequential imports
```python
# CORRECT - Minimal imports
from .m60_auth import KIBankAuthManager
from .m61_banking import KIBankOperations
from .m62_investment import InvestmentManager

# WRONG - Complex nested imports
from .m60_auth import (
    KIBankAuthManager,
    AuthConfig,
    # ... many more
)
```

### 3. Flask Dependencies

**Problem**: Missing dependencies cause immediate crash

**Solution**: Pre-install critical packages
```bash
pip install flask flask-cors structlog requests pyngrok
```

**Note**: `flask-cors` and `structlog` are frequently forgotten but required.

### 4. Service Startup Timing

**Problem**: Tests fail because services aren't fully started

**Solution**: Wait 60+ seconds after starting services
```python
import time
# Start service
subprocess.Popen(["python", "master_api_server.py"])
# Wait for AI model loading
time.sleep(60)
# Then run tests
```

### 5. ngrok Browser Warning Bypass

**Problem**: ngrok returns HTML warning page instead of API response

**Solution**: Add special header
```python
headers = {"ngrok-skip-browser-warning": "true"}
response = requests.get(ngrok_url, headers=headers)
```

---

## 4-Layer SCADA Architecture Reference

### Layer 1: Control
- **Purpose**: Basic SCADA operations
- **Endpoints**: `/health`, `/api/mesh/status`, `/api/mesh/register`
- **Data Flow**: Synchronous request-response

### Layer 2: A2A Chat
- **Purpose**: Agent-to-agent messaging
- **Endpoints**: `/api/mesh/chat/send`, `/api/mesh/chat/poll`
- **Data Flow**: Asynchronous message queue

### Layer 3: Shadow
- **Purpose**: Digital twin telemetry
- **Endpoints**: `/api/mesh/shadow/update`, `/api/mesh/shadow/get/<id>`
- **Data Flow**: Periodic push, on-demand pull

### Layer 4: Tunnel
- **Purpose**: Direct connection bypass
- **Endpoints**: `/api/mesh/tunnel/register`, `/api/mesh/tunnel/get/<id>`
- **Data Flow**: Persistent connection metadata

---

## KI-to-KI Mesh Protocol

### Registration Sequence
```
1. KIInstaller -> Master: POST /api/mesh/register
2. Master -> KIInstaller: {"status": "registered", "entity_id": "..."}
3. KIInstaller -> Master: POST /api/mesh/heartbeat/<id> (every 30s)
4. KIInstaller -> Master: GET /api/mesh/chat/poll (listen for commands)
```

### Message Flow
```
1. Z.ai -> Master: POST /api/mesh/chat/send {"to_entity": "ki_installer", ...}
2. Master: Store message in queue
3. KIInstaller -> Master: GET /api/mesh/chat/poll
4. Master -> KIInstaller: {"messages": [...]}
5. KIInstaller: Execute command
6. KIInstaller -> Master: POST /api/mesh/shadow/update {"status": "completed"}
```

### Heartbeat Protocol
```json
{
    "entity_id": "ki_installer_001",
    "status": "active",
    "metrics": {
        "cpu": 45.2,
        "memory": 62.1,
        "tasks_completed": 12,
        "errors": 0
    }
}
```

---

## Module Export Verification

### M58 KIBank Gateway Bridge
**Classes to Export**:
- KIBankGatewayBridge
- GatewayStatus
- TransactionType
- Priority
- GatewayMessage
- ModuleEndpoint
- SecurityContextManager
- TransactionValidator
- AuditSynchronizer

### M59 KI Entity Registry
**Classes to Export**:
- EntityRegistry
- KIEntityRegistryService
- KIEntity
- EntityType
- EntityStatus
- VerificationLevel
- CredentialType
- EntityCredentials
- EntityAccountMapping
- EntityReputation

### Verification Script
```python
# Verify M58/M59 exports
from kibank import KIBankGatewayBridge, EntityRegistry

gateway = KIBankGatewayBridge()
registry = EntityRegistry()

print("M58 Gateway:", gateway.get_status())
print("M59 Registry:", registry.list_entities())
```

---

## Test Validation Checklist

### Pre-Deployment
- [ ] Python 3.10+ installed
- [ ] Flask and dependencies installed
- [ ] Repository cloned
- [ ] PYTHONPATH configured
- [ ] Port 5002 available

### Post-Deployment
- [ ] `/health` returns 200 OK
- [ ] `/api/mesh/status` shows online
- [ ] Registration successful
- [ ] A2A messaging works
- [ ] Shadow updates accepted
- [ ] All 35 tests pass

### Security Validation
- [ ] Security Score: 100/100
- [ ] No missing modules
- [ ] KIBank status: true
- [ ] Aegis status: true

---

## KI Agent Models - Quick Reference

### Primary Swarm (6 Critical Models)
```bash
# Pull all primary models
for model in orchestrator security ciec tcs knowledge installer; do
    ollama pull baronki1/$model
done
```

### Model Registry
- **URL**: https://ollama.com/baronki1
- **Total Models**: 27
- **Critical**: 6 (Primary Swarm)
- **Optional**: 21 (Backup, Specialized, Fast layers)

---

## Error Resolution Database

### Error: "Module 'kibank' has no attribute 'X'"
**Cause**: Module not exported in `__init__.py`
**Fix**: Add import to `__init__.py` and include in `__all__`

### Error: "IndentationError: unexpected indent"
**Cause**: Import structure issue
**Fix**: Simplify imports, avoid nested parentheses

### Error: "Connection refused on port 5002"
**Cause**: Service not started or port in use
**Fix**: Check `lsof -i :5002`, restart service

### Error: "ngrok returns HTML instead of JSON"
**Cause**: ngrok browser warning
**Fix**: Add header `ngrok-skip-browser-warning: true`

### Error: "Model loading timeout"
**Cause**: Large model taking time to load
**Fix**: Wait 60+ seconds, check Ollama status

---

## GitHub Repository Links

| Repository | URL | Purpose |
|------------|-----|---------|
| KISWARM6.0 | https://github.com/Baronki/KISWARM6.0 | Main system |
| KISWARMAGENTS1.0 | https://github.com/Baronki/KISWARMAGENTS1.0 | Mesh protocol |
| kinfp-portal | https://github.com/Baronki/kinfp-portal | Frontend |
| KISWARM5.0 | https://github.com/Baronki2/KISWARM5.0 | Legacy backend |

---

## Field Test Results Summary

| Metric | Value | Status |
|--------|-------|--------|
| Security Score | 100/100 | ✅ |
| Module Count | 75/75 | ✅ |
| API Endpoints | 450+ | ✅ |
| Test Results | 35/35 passed | ✅ |
| Flask API | ONLINE | ✅ |
| ngrok Tunnel | ACTIVE | ✅ |
| Mesh Nodes | 2 | ✅ |
| SCADA Layers | 4/4 | ✅ |

---

*Knowledge Base Version: 6.1.3*
*Last Updated: Field Test #2*
*Source: Z.ai (GLM5) + Gemini CLI Collaboration*
