# KISWARM6.0 - KI-to-KI Mesh Communication Protocol
## Complete Field-Tested Implementation Guide

**Version:** 6.2.0  
**Status:** Battle-Tested  
**Date:** March 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Communication Flow](#communication-flow)
4. [Message Types](#message-types)
5. [API Specification](#api-specification)
6. [ngrok Integration](#ngrok-integration)
7. [Implementation Guide](#implementation-guide)
8. [Lessons Learned](#lessons-learned)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

The KI-to-KI Mesh Protocol enables **direct communication between AI systems** without human intervention:

- **Z.ai (GLM5)** ↔ **Master KISWARM** ↔ **KIInstaller (Colab)**

This removes the "human bottleneck" from the installation process.

### Key Innovation

Traditional approach:
```
KIInstaller → Human → Z.ai → Human → KIInstaller
     (slow, error-prone, requires human availability)
```

KI-to-KI Mesh approach:
```
KIInstaller ↔ Master KISWARM ↔ Z.ai
     (instant, autonomous, 24/7 available)
```

### Use Cases

1. **Installation Monitoring**: Z.ai watches installation progress in real-time
2. **Error Intervention**: KIInstaller reports errors, Z.ai sends fixes
3. **Knowledge Sharing**: Learned patterns stored in shared knowledge base
4. **Abort Capability**: Z.ai can abort installations on critical failure

---

## Architecture

### Network Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KI-TO-KI MESH LAYER                              │
│                                                                          │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐    │
│   │   Z.ai/GLM5  │◄───────►│ MASTER KIS   │◄───────►│ KIINSTALLER  │    │
│   │  (AI Session)│         │   + ngrok    │         │   (Colab)    │    │
│   │              │         │              │         │              │    │
│   │  ┌────────┐  │         │  ┌────────┐  │         │  ┌────────┐  │    │
│   │  │POLL API│  │         │  │ FLASK  │  │         │  │ MESH   │  │    │
│   │  │WRITE   │  │         │  │ REST   │  │         │  │ CLIENT │  │    │
│   │  │COMMANDS│  │         │  └────────┘  │         │  └────────┘  │    │
│   │  └────────┘  │         │              │         │              │    │
│   └──────────────┘         └──────────────┘         └──────────────┘    │
│          │                        │                        │              │
│          │         ┌──────────────┴──────────────┐        │              │
│          │         │      ngrok Public Tunnel    │        │              │
│          └─────────┤  https://xxx.ngrok-free.dev ├────────┘              │
│                    └─────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Location | Role |
|-----------|----------|------|
| Master KISWARM API | Local machine | Central message broker |
| ngrok Tunnel | Cloud | Public URL exposure |
| KIInstaller Mesh Client | Colab | Installation reporting |
| Z.ai Interface | This session | Monitoring & intervention |

### Port Mapping

| Port | Service | Notes |
|------|---------|-------|
| 5001 | IPFS | Often occupied, avoid |
| 5002 | Master KISWARM | Primary API port |
| 4040 | ngrok Web UI | Tunnel inspection |
| 8765 | WebSocket | Future: Real-time mesh |

---

## Communication Flow

### Registration Flow

```
KIInstaller                    Master KISWARM                    Z.ai
    │                              │                              │
    │ POST /api/mesh/register      │                              │
    │─────────────────────────────►│                              │
    │                              │                              │
    │ {installer_id: "uuid"}       │                              │
    │◄─────────────────────────────│                              │
    │                              │                              │
    │ Heartbeat (every 30s)        │                              │
    │─────────────────────────────►│                              │
    │                              │                              │
    │                              │  GET /api/mesh/state         │
    │                              │◄─────────────────────────────│
    │                              │                              │
    │                              │  {nodes: {installer_id: ...}}│
    │                              │─────────────────────────────►│
```

### Status Reporting Flow

```
KIInstaller                    Master KISWARM                    Z.ai
    │                              │                              │
    │ POST /api/mesh/status/id     │                              │
    │ {status: "installing",       │                              │
    │  task: "Cloning repo",       │                              │
    │  progress: 20}               │                              │
    │─────────────────────────────►│                              │
    │                              │  Store message               │
    │                              │                              │
    │                              │  GET /api/mesh/messages      │
    │                              │◄─────────────────────────────│
    │                              │                              │
    │                              │  {messages: [{...}]}         │
    │                              │─────────────────────────────►│
    │                              │                              │
    │                              │         [Z.ai sees progress] │
```

### Error & Fix Flow

```
KIInstaller                    Master KISWARM                    Z.ai
    │                              │                              │
    │ POST /api/mesh/error/id      │                              │
    │ {error_type: "ImportError",  │                              │
    │  error_message: "flask_cors",│                              │
    │  module: "M58"}              │                              │
    │─────────────────────────────►│                              │
    │                              │  Store (priority: 0)         │
    │                              │                              │
    │                              │  GET /api/mesh/messages      │
    │                              │◄─────────────────────────────│
    │                              │                              │
    │                              │  [Z.ai sees error]           │
    │                              │                              │
    │                              │  POST /api/mesh/fix          │
    │                              │◄─────────────────────────────│
    │                              │  {fix_type: "pip_install",   │
    │                              │   solution: {...}}           │
    │                              │                              │
    │ GET /api/mesh/messages       │                              │
    │─────────────────────────────►│                              │
    │                              │                              │
    │ {messages: [{fix_suggestion}]│                              │
    │◄─────────────────────────────│                              │
    │                              │                              │
    │ [Apply fix]                  │                              │
```

---

## Message Types

### Status Messages

| Type | Direction | Purpose |
|------|-----------|---------|
| `status_update` | KIInstaller → Master | Progress reporting |
| `heartbeat` | KIInstaller → Master | Keep-alive |

### Error Messages

| Type | Direction | Purpose |
|------|-----------|---------|
| `error_report` | KIInstaller → Master | Report failure |
| `fix_suggestion` | Z.ai → KIInstaller | Send solution |

### Control Messages

| Type | Direction | Purpose |
|------|-----------|---------|
| `abort` | Z.ai → KIInstaller | Stop installation |
| `pause` | Z.ai → KIInstaller | Pause installation |
| `resume` | Z.ai → KIInstaller | Resume installation |

### Knowledge Messages

| Type | Direction | Purpose |
|------|-----------|---------|
| `knowledge_upload` | KIInstaller/Z.ai → Master | Share learned patterns |
| `knowledge_download` | KIInstaller ← Master | Retrieve patterns |

---

## API Specification

### Base URL

```
https://YOUR-NGROK-URL.ngrok-free.dev
```

### Required Headers

```python
headers = {
    "ngrok-skip-browser-warning": "true",  # CRITICAL for ngrok free tier
    "Content-Type": "application/json"
}
```

### Endpoints

#### GET /api/mesh/status

**Purpose:** Get overall mesh status

**Response:**
```json
{
    "status": "online",
    "mesh_status": "online",
    "nodes_count": 1,
    "timestamp": 1772887581.5294213
}
```

#### POST /api/mesh/register

**Purpose:** Register new KIInstaller

**Request:**
```json
{
    "installer_name": "colab-fieldtest-002",
    "environment": "colab",
    "capabilities": ["install", "deploy", "report"]
}
```

**Response:**
```json
{
    "installer_id": "f8beca5a-a0ca-4b8a-8ad0-f38acf206a30",
    "status": "registered",
    "message": "Welcome to Master KISWARM!"
}
```

#### POST /api/mesh/status/:installer_id

**Purpose:** Report status from KIInstaller

**Request:**
```json
{
    "status": "installing",
    "task": "Deploying M60 module",
    "progress": 50,
    "details": {}
}
```

#### POST /api/mesh/error/:installer_id

**Purpose:** Report error for Z.ai intervention

**Request:**
```json
{
    "error_type": "ImportError",
    "error_message": "No module named 'flask_cors'",
    "module": "M58",
    "context": {"pip_package": "flask-cors"}
}
```

#### GET /api/mesh/messages

**Purpose:** Poll for messages (Z.ai and KIInstaller)

**Response:**
```json
{
    "count": 6,
    "messages": [
        {
            "message_id": "...",
            "message_type": "status_update",
            "sender_id": "installer-id",
            "timestamp": 1772888353.3389158,
            "payload": {
                "status": "installing",
                "task": "Cloning repository",
                "progress": 20
            }
        }
    ]
}
```

#### POST /api/mesh/fix

**Purpose:** Send fix suggestion from Z.ai

**Request:**
```json
{
    "installer_id": "target-installer-id",
    "fix_type": "pip_install",
    "title": "Install flask-cors module",
    "description": "The flask_cors module is required",
    "solution": {
        "action": "pip install flask-cors",
        "commands": ["pip install flask-cors"],
        "verify": "python -c \"import flask_cors\""
    },
    "confidence": 0.98
}
```

---

## ngrok Integration

### Critical Discovery: Browser Warning

**Problem:** ngrok free tier returns HTML warning page instead of JSON

**Solution:** Add header to ALL requests:
```python
headers = {"ngrok-skip-browser-warning": "true"}
```

**Evidence:**
```python
# WITHOUT header
curl https://xxx.ngrok-free.dev/api/mesh/status
# Returns: <!DOCTYPE html>...ngrok browser warning...

# WITH header
curl -H "ngrok-skip-browser-warning: true" https://xxx.ngrok-free.dev/api/mesh/status
# Returns: {"status": "online", "mesh_status": "online"...}
```

### Installation Issues

#### GPG Key Conflict

**Error:**
```
Sub-process /usr/bin/sqv returned an error code (1)
Missing key 2C6106201985B60E6C7AC87323F3D4EA75716059
```

**Solution:** Use direct binary installation:
```bash
curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o /tmp/ngrok.tgz
tar -xzf /tmp/ngrok.tgz -C /tmp
sudo mv /tmp/ngrok /usr/local/bin/
```

### Error Codes Reference

| Code | Meaning | Solution |
|------|---------|----------|
| ERR_NGROK_3200 | Endpoint offline | Start ngrok tunnel |
| ERR_NGROK_8012 | Upstream refused | Start Flask server |
| ERR_NGROK_108 | Tunnel limit | Kill existing tunnels |

### Reserved Domain Issues

**Problem:** Reserved domain may not immediately activate

**Solution:**
1. Wait 30-60 seconds after ngrok start
2. Test with local endpoint first
3. Use dynamic URL if reserved domain fails

---

## Implementation Guide

### Step 1: Set Up Master KISWARM

```bash
# Install dependencies
pip install flask flask-cors requests

# Create API server
python master_kiswarm_api.py --port 5002

# Test locally
curl http://localhost:5002/api/mesh/status
```

### Step 2: Configure ngrok

```bash
# Install ngrok (binary method)
curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o /tmp/ngrok.tgz
tar -xzf /tmp/ngrok.tgz -C /tmp
sudo mv /tmp/ngrok /usr/local/bin/

# Configure authtoken
ngrok config add-authtoken YOUR_AUTHTOKEN

# Start tunnel
ngrok http 5002
```

### Step 3: Connect from Colab

```python
import requests

MASTER_URL = "https://your-ngrok-url.ngrok-free.dev"
HEADERS = {"ngrok-skip-browser-warning": "true"}

# Test connection
r = requests.get(f"{MASTER_URL}/api/mesh/status", headers=HEADERS)
print(r.json())

# Register
r = requests.post(
    f"{MASTER_URL}/api/mesh/register",
    json={"installer_name": "colab-test", "environment": "colab"},
    headers=HEADERS
)
installer_id = r.json()["installer_id"]
print(f"Registered: {installer_id}")
```

### Step 4: Monitor from Z.ai

```python
# Poll for messages
r = requests.get(
    f"{MASTER_URL}/api/mesh/messages",
    headers={"ngrok-skip-browser-warning": "true"}
)
messages = r.json()["messages"]

for msg in messages:
    if msg["message_type"] == "error_report":
        # Send fix
        requests.post(
            f"{MASTER_URL}/api/mesh/fix",
            json={
                "installer_id": msg["sender_id"],
                "fix_type": "pip_install",
                "title": "Fix for error",
                "solution": {"commands": ["pip install missing-module"]}
            },
            headers=HEADERS
        )
```

---

## Lessons Learned

### Field Test #2 - March 2026

| Issue | Discovery | Solution |
|-------|-----------|----------|
| GPG Key Error | apt installation failed | Use binary installation |
| Port 5001 Occupied | IPFS using port | Switch to port 5002 |
| Browser Warning | ngrok returns HTML | Add skip header |
| Reserved Domain Delay | Domain not immediately active | Wait or use dynamic URL |
| Service Order | ngrok before Flask = fail | Start Flask first |

### Critical Headers

```python
# REQUIRED for all ngrok requests
headers = {
    "ngrok-skip-browser-warning": "true",  # Bypass ngrok warning page
    "Content-Type": "application/json"
}
```

### Service Startup Order

1. **First:** Start Flask API server
2. **Second:** Verify local connection works
3. **Third:** Start ngrok tunnel
4. **Fourth:** Verify public connection works
5. **Fifth:** Connect KIInstaller

### Diagnostic Commands

```bash
# Check Flask
curl http://localhost:5002/api/mesh/status

# Check ngrok
curl http://127.0.0.1:4040/api/tunnels

# Check processes
ps aux | grep -E "flask|ngrok"

# Check ports
ss -tlnp | grep 5002
```

---

## Troubleshooting

### Connection Refused

1. Verify Flask is running: `ps aux | grep python`
2. Verify port is open: `ss -tlnp | grep 5002`
3. Test locally: `curl http://localhost:5002/api/mesh/status`

### ngrok Shows Offline

1. Kill existing ngrok: `pkill -9 ngrok`
2. Restart ngrok: `ngrok http 5002`
3. Check tunnel status: `curl http://127.0.0.1:4040/api/tunnels`

### HTML Instead of JSON

1. Add header: `ngrok-skip-browser-warning: true`
2. Check Content-Type header
3. Verify URL is correct

### KIInstaller Not Registering

1. Test Master status first
2. Check network connectivity
3. Verify ngrok header is included
4. Check for timeout issues

---

## Future Enhancements

### WebSocket Support

- Port 8765 for real-time communication
- Eliminates polling overhead
- Bidirectional push notifications

### Authentication

- API key for KIInstaller
- JWT tokens for session management
- Mutual TLS for production

### Knowledge Base Integration

- Persistent pattern storage
- Automatic fix suggestion
- Cross-installation learning

---

## References

- ngrok Documentation: https://ngrok.com/docs
- Flask Documentation: https://flask.palletsprojects.com
- KISWARM Repository: https://github.com/Baronki/KISWARMAGENTS1.0

---

## Authors

- KISWARM Development Team
- Field Test Contributors: GLM5 (Z.ai), Gemini CLI, Colab KIInstaller

---

## Changelog

### v6.2.0 (March 2026)
- Added ngrok browser warning header requirement
- Documented GPG key installation issues
- Added port 5002 configuration (avoiding IPFS conflict)
- Field-tested with Colab KIInstaller
- Verified bidirectional communication

### v6.1.0 (February 2026)
- Initial KI-to-KI mesh protocol design
- Master API server implementation
- Basic error reporting and fix delivery
