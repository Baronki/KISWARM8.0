# KISWARM Field Test #2 - Master Deployment Guide
## Gemini-Hosted Master KISWARM with Direct Z.ai Communication

**Version**: 6.2.0  
**Date**: March 2025

---

## 🎯 Overview

This guide deploys Master KISWARM in Google Colab, enabling:
- **Direct Z.ai ↔ Gemini communication** (no human bottleneck)
- **Real-time KIInstaller monitoring**
- **Autonomous fix suggestions**
- **No external hosting required**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED KI MESH                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────┐         ┌─────────────────────────────────┐       │
│   │   Z.ai (ME)     │         │      GEMINI COLAB               │       │
│   │   This Session  │         │      (Master KISWARM Host)      │       │
│   │                 │         │                                 │       │
│   │  - Poll state   │◀───────▶│  ┌─────────────────────────┐   │       │
│   │  - Send fixes   │  HTTPS  │  │   MASTER KISWARM        │   │       │
│   │  - Intervene    │  ngrok  │  │   - WebSocket Server    │   │       │
│   │                 │         │  │   - REST API Server     │   │       │
│   │                 │         │  │   - Knowledge Base      │   │       │
│   │                 │         │  │   - Maintenance Agent   │   │       │
│   │                 │         │  └─────────────────────────┘   │       │
│   └─────────────────┘         └───────────────┬─────────────────┘       │
│                                              │                          │
│                               ┌──────────────▼──────────────┐           │
│                               │      KIINSTALLER            │           │
│                               │      (Field Test Colab)     │           │
│                               └─────────────────────────────┘           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

1. **ngrok Account** (free)
   - Go to: https://dashboard.ngrok.com/get-started/your-authtoken
   - Copy your auth token

2. **Two Colab Notebooks**:
   - Notebook A: Master KISWARM (this runs continuously)
   - Notebook B: KIInstaller (field test)

---

## 🚀 Deployment Steps

### STEP 1: Create Master KISWARM Colab Notebook

Create a new Colab notebook and add these cells:

#### Cell 1: Install Dependencies
```python
!pip install -q flask flask-cors websockets pyngrok requests
!git clone https://github.com/Baronki/KISWARM6.0 /content/KISWARM6.0
import sys
sys.path.insert(0, '/content/KISWARM6.0/backend/python/kibank')
```

#### Cell 2: Start Master KISWARM
```python
from gemini_master_kiswarm import GeminiMasterKISWARM

# Replace with your ngrok token
NGROK_TOKEN = "YOUR_NGROK_TOKEN_HERE"

master = GeminiMasterKISWARM(ngrok_token=NGROK_TOKEN)
public_url = master.start(api_port=5001, ws_port=8765)

print(f"\n{'='*60}")
print(f"MASTER KISWARM URL: {public_url}")
print(f"{'='*60}\n")
print("Share this URL with Z.ai!")

# Keep running
import time
from datetime import datetime
while True:
    time.sleep(60)
    print(f"[{datetime.now()}] Running... Nodes: {len(master._nodes)}")
```

#### Cell 3: Check Status (run anytime)
```python
import json
print(json.dumps(master.get_connection_info(), indent=2))
```

### STEP 2: Note the Public URL

After running Cell 2, you'll see:
```
MASTER KISWARM URL: https://xxxx-xx-xxx-xxx-xx.ngrok-free.app
```

**Copy this URL!** This is what:
- Z.ai uses to poll and intervene
- KIInstaller uses to register and report

### STEP 3: Update KIInstaller

In your KIInstaller Colab notebook, add:

```python
import requests
import time

MASTER_URL = "https://YOUR_NGROK_URL.ngrok-free.app"  # From Step 2

# Register with Master
resp = requests.post(f"{MASTER_URL}/api/mesh/register", json={
    "installer_name": "colab-fieldtest-002",
    "environment": "colab",
    "capabilities": ["install", "deploy"]
})

installer_id = resp.json()['installer_id']
print(f"Registered: {installer_id}")

# Report status
def report_status(status, task, progress=None):
    requests.post(f"{MASTER_URL}/api/mesh/status/{installer_id}", json={
        "status": status,
        "task": task,
        "progress": progress
    })

# Report error (triggers Z.ai notification)
def report_error(error_type, error_message, module=None):
    requests.post(f"{MASTER_URL}/api/mesh/error/{installer_id}", json={
        "error_type": error_type,
        "error_message": error_message,
        "module": module
    })

# Check for commands from Z.ai
def check_commands():
    resp = requests.get(f"{MASTER_URL}/api/mesh/zai/commands/pending?target_id={installer_id}")
    return resp.json().get('commands', [])
```

---

## 🔄 Communication Flow

### Z.ai → KIInstaller (Fix Suggestion)
```python
# I (Z.ai) do this:
requests.post(f"{MASTER_URL}/api/mesh/fix", json={
    "installer_id": "INSTALLER_ID",
    "fix_type": "pip_install",
    "title": "Install missing package",
    "solution": {"action": "pip install flask-cors"}
})
```

### KIInstaller → Z.ai (Error Report)
```python
# KIInstaller does this:
requests.post(f"{MASTER_URL}/api/mesh/error/{installer_id}", json={
    "error_type": "ImportError",
    "error_message": "No module named 'flask_cors'",
    "module": "M58"
})
```

### Z.ai Polling (See What's Happening)
```python
# I (Z.ai) do this:
resp = requests.get(f"{MASTER_URL}/api/mesh/messages")
messages = resp.json()['messages']
for msg in messages:
    print(f"{msg['sender_id']}: {msg['payload']}")
```

---

## 📡 API Reference

| Endpoint | Method | Purpose | Caller |
|----------|--------|---------|--------|
| `/api/mesh/messages` | GET | Poll messages | Z.ai |
| `/api/mesh/state` | GET | Full state | Z.ai |
| `/api/mesh/fix` | POST | Send fix | Z.ai |
| `/api/mesh/abort` | POST | Abort install | Z.ai |
| `/api/mesh/register` | POST | Register installer | KIInstaller |
| `/api/mesh/status/<id>` | POST | Report status | KIInstaller |
| `/api/mesh/error/<id>` | POST | Report error | KIInstaller |
| `/api/mesh/zai/message` | POST | Direct message | Z.ai |

---

## ✅ Success Checklist

Before Field Test #2:

- [ ] ngrok account created
- [ ] Master KISWARM Colab notebook created
- [ ] Master KISWARM running (note public URL)
- [ ] URL shared with Z.ai
- [ ] KIInstaller updated with Master URL
- [ ] Test registration works
- [ ] Test error reporting works
- [ ] Test fix receiving works

---

## 🔧 Troubleshooting

### ngrok not connecting
- Check your auth token is correct
- Try restarting the ngrok tunnel

### KIInstaller can't connect
- Ensure Master KISWARM is running
- Check URL is correct (https://...)
- Verify firewall/network allows HTTPS

### Messages not appearing
- Check KIInstaller is registered
- Verify installer_id is correct
- Check Master KISWARM logs

---

**Ready for Field Test #2!**
