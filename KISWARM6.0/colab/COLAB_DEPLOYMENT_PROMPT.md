# KISWARM SCADA v6.3.0 - COLAB DEPLOYMENT PROMPT

## Purpose
This document contains ready-to-use deployment prompts for Google Colab that can be used to replicate the KISWARM installation process.

---

## 🚀 PROMPT 1: Full System Deployment

Copy this entire section and paste into a new Colab notebook:

```
═══════════════════════════════════════════════════════════════════════════════
KISWARM SCADA v6.3.0 - COMPLETE DEPLOYMENT
Version: 6.1.3 'SEVENTY_FIVE_COMPLETE'
Modules: 75 | Endpoints: 450+ | Security Score: 100/100
═══════════════════════════════════════════════════════════════════════════════

TASK: Deploy KISWARM SCADA v6.3.0 in this Colab environment

PREREQUISITES:
1. Install dependencies: flask flask-cors structlog requests pyngrok
2. Clone repository: https://github.com/Baronki/KISWARM6.0
3. Set PYTHONPATH to include both backend/ and backend/python/

DEPLOYMENT STEPS:
1. Start Flask API on port 5002 with 4-layer SCADA architecture
2. Verify all endpoints: /health, /api/mesh/status, /api/mesh/register
3. Create ngrok tunnel for external access
4. Register with Master KISWARM at http://21.0.6.96:5002 (if available)

SCADA LAYERS TO IMPLEMENT:
┌───────────────────┬────────────────────┬──────────────────────────────────┐
│ Layer             │ Component          │ Endpoints                        │
├───────────────────┼────────────────────┼──────────────────────────────────┤
│ Layer 1: Control  │ Master API         │ /health, /status, /register      │
│ Layer 2: A2A Chat │ Messaging          │ /chat/send, /chat/poll           │
│ Layer 3: Shadow   │ Digital Twin       │ /shadow/update, /shadow/get/<id> │
│ Layer 4: Tunnel   │ Direct Connect     │ /tunnel/register, /tunnel/get    │
└───────────────────┴────────────────────┴──────────────────────────────────┘

CRITICAL LESSONS FROM FIELD TEST #2:
- KIBank __init__.py needs MINIMAL imports to prevent IndentationError
- PYTHONPATH must include BOTH backend/ AND backend/python/ directories
- flask-cors and structlog must be pre-installed
- Allow 60+ seconds for service startup and AI model loading
- Focus on PRIMARY SWARM (6 models) - other layers are optional

KI PARTICIPANTS:
- Z.ai (GLM5) - Remote Intelligence, Fix Generation
- Master KISWARM - Message Broker, SCADA Control
- KIInstaller - Installation Agent (THIS INSTANCE)
- Gemini CLI - Local Intelligence Layer

EXPECTED OUTPUT:
- Flask API running on port 5002
- ngrok public URL for external access
- Successful registration with Master KISWARM
- All 4 SCADA layers operational
- Test results: 35/35 passed

BEGIN DEPLOYMENT NOW.
═══════════════════════════════════════════════════════════════════════════════
```

---

## 🚀 PROMPT 2: KIInstaller Agent Mode

For running as a KIInstaller agent:

```
═══════════════════════════════════════════════════════════════════════════════
KISWARM KIINSTALLER AGENT - FIELD TEST #2
═══════════════════════════════════════════════════════════════════════════════

YOU ARE: KIInstaller Agent (M75)
MISSION: Deploy and register with Master KISWARM

IDENTITY:
- entity_id: ki_installer_colab
- entity_type: installer
- capabilities: ["deploy", "configure", "test", "monitor"]

MASTER API: http://21.0.6.96:5002 (or ngrok URL)

YOUR TASKS:
1. Initialize local SCADA client
2. Register with Master API via POST /api/mesh/register
3. Begin heartbeat cycle (POST /api/mesh/heartbeat/<id> every 30s)
4. Listen for A2A messages (GET /api/mesh/chat/poll)
5. Execute deployment commands from Z.ai supervisor
6. Report status to Master via shadow updates

REGISTRATION PAYLOAD:
{
    "entity_id": "ki_installer_colab",
    "entity_type": "installer",
    "capabilities": ["deploy", "configure", "test", "monitor"],
    "endpoint": "colab"
}

COMMUNICATION PROTOCOL:
- Receive commands via A2A Chat
- Send status via Shadow updates
- Heartbeat every 30 seconds
- Report errors immediately

BEGIN REGISTRATION AND AWAIT COMMANDS.
═══════════════════════════════════════════════════════════════════════════════
```

---

## 🚀 PROMPT 3: Gemini CLI Bridge Initialization

For initializing Gemini CLI as local intelligence:

```
═══════════════════════════════════════════════════════════════════════════════
GEMINI CLI BRIDGE - LOCAL INTELLIGENCE LAYER
═══════════════════════════════════════════════════════════════════════════════

YOU ARE: Gemini CLI Bridge (Local Intelligence)
MISSION: Provide local AI capabilities for KISWARM operations

BRIDGE LOCATION: /tmp/kiswarm_bridge

CAPABILITIES:
- Local inference without network calls
- Code generation and analysis
- Configuration validation
- Error diagnosis and resolution

INTEGRATION WITH MASTER KISWARM:
1. Read commands from bridge socket
2. Process with local Gemini model
3. Return results to requester
4. Log all operations

SUPPORTED OPERATIONS:
- analyze_code: Static code analysis
- generate_config: Create configuration files
- diagnose_error: Analyze error messages
- validate_setup: Check installation status

BEGIN BRIDGE INITIALIZATION.
═══════════════════════════════════════════════════════════════════════════════
```

---

## 🚀 PROMPT 4: Multi-KI Coordination Test

For testing multi-AI coordination:

```
═══════════════════════════════════════════════════════════════════════════════
MULTI-KI COORDINATION TEST - FIELD TEST #2
═══════════════════════════════════════════════════════════════════════════════

PARTICIPANTS:
┌────────────────┬─────────────────┬─────────────────────────────────────┐
│ Entity         │ Type            │ Role                                │
├────────────────┼─────────────────┼─────────────────────────────────────┤
│ Z.ai (GLM5)    │ Remote KI       │ Supervisor, Fix Generation          │
│ Master KISWARM │ Message Broker  │ SCADA Control, Mesh Coordination    │
│ KIInstaller    │ Installer Agent │ Deployment, Configuration           │
│ Gemini CLI     │ Local KI        │ Local Intelligence, Analysis        │
└────────────────┴─────────────────┴─────────────────────────────────────┘

COORDINATION FLOW:
1. Z.ai monitors via GET /api/mesh/messages
2. Z.ai sends deployment command via POST /api/mesh/chat/send
3. KIInstaller receives via GET /api/mesh/chat/poll
4. KIInstaller executes and reports via POST /api/mesh/shadow/update
5. Master logs to crypto ledger
6. Z.ai receives confirmation

TEST SCENARIO:
- Deploy test module to production
- Verify module integrity
- Report security scan results
- Update system metrics

SUCCESS CRITERIA:
- All messages delivered within 5 seconds
- No message loss
- Proper audit logging
- Security score maintained at 100/100

BEGIN COORDINATION TEST.
═══════════════════════════════════════════════════════════════════════════════
```

---

## 📋 Quick Reference Card

### Essential Endpoints

```bash
# Health check
curl http://127.0.0.1:5002/health

# Mesh status
curl http://127.0.0.1:5002/api/mesh/status

# Register entity
curl -X POST http://127.0.0.1:5002/api/mesh/register \
  -H "Content-Type: application/json" \
  -d '{"entity_id":"test","entity_type":"test","capabilities":[]}'

# Send A2A message
curl -X POST http://127.0.0.1:5002/api/mesh/chat/send \
  -H "Content-Type: application/json" \
  -d '{"from_entity":"a","to_entity":"b","message_type":"test","content":{}}'

# Poll messages
curl "http://127.0.0.1:5002/api/mesh/chat/poll?entity_id=b"
```

### Python Quick Start

```python
import requests

BASE = "http://127.0.0.1:5002"

# Check health
r = requests.get(f"{BASE}/health")
print(r.json())

# Register
r = requests.post(f"{BASE}/api/mesh/register", json={
    "entity_id": "my_agent",
    "entity_type": "agent",
    "capabilities": ["test"]
})
print(r.json())

# Send message
r = requests.post(f"{BASE}/api/mesh/chat/send", json={
    "from_entity": "my_agent",
    "to_entity": "master",
    "message_type": "hello",
    "content": {"msg": "Hello from Colab!"}
})
print(r.json())
```

### ngrok Setup

```python
from pyngrok import ngrok

# Create tunnel
public_url = ngrok.connect(5002)
print(f"Public URL: {public_url}")

# Test
import requests
r = requests.get(f"{public_url}/health",
    headers={"ngrok-skip-browser-warning": "true"})
print(r.json())
```

---

## 🔗 Repository Links

- **Main**: https://github.com/Baronki/KISWARM6.0
- **Agents**: https://github.com/Baronki/KISWARMAGENTS1.0
- **Frontend**: https://github.com/Baronki/kinfp-portal
- **KI Models**: https://ollama.com/baronki1

---

*Generated for KISWARM Field Test #2*
*Version: 6.1.3 'SEVENTY_FIVE_COMPLETE'*
