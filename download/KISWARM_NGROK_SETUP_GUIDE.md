# KISWARM6.0 - ngrok Setup Guide for Master KISWARM
## Complete Field-Tested Installation Documentation

**Version:** 6.2.0  
**Status:** Battle-Tested  
**Last Updated:** March 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Installation](#step-by-step-installation)
4. [Common Issues & Solutions](#common-issues--solutions)
5. [Architecture](#architecture)
6. [API Reference](#api-reference)
7. [Colab Integration](#colab-integration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide documents the complete setup process for establishing a KI-to-KI Mesh Communication channel between:
- **Master KISWARM** (running on your local machine)
- **KIInstaller** (running in Google Colab)
- **Z.ai/GLM5** (this AI session)

### Key Discovery: ngrok Browser Warning

**CRITICAL**: ngrok free tier displays a browser warning page. All API requests MUST include:

```python
headers = {"ngrok-skip-browser-warning": "true"}
```

Without this header, requests return HTML instead of JSON, causing connection failures.

---

## Prerequisites

### System Requirements
- Python 3.8+
- curl
- sudo access (for ngrok installation)

### ngrok Account
- Sign up at https://ngrok.com
- Link to GitHub account (Baronki)
- Obtain authtoken from dashboard

### Current ngrok Configuration
- **Authtoken**: `3Ac51HC51vmerRvn9CodFhxgnYN_771JYNNWUuwi4uQyucxHx`
- **Reserved Domain**: `https://brenton-distinctive-iodometrically.ngrok-free.dev`

---

## Step-by-Step Installation

### Method 1: Direct Binary Installation (Recommended)

The apt repository method failed due to GPG key conflicts. Use direct binary installation:

```bash
# Download ngrok binary for Linux amd64
curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o /tmp/ngrok.tgz

# Extract and install
tar -xzf /tmp/ngrok.tgz -C /tmp
sudo mv /tmp/ngrok /usr/local/bin/

# Verify installation
ngrok version
# Expected: ngrok version 3.37.1
```

### Method 2: Apt Installation (If GPG Keys Work)

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null

echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list

sudo apt update
sudo apt install ngrok
```

### Configure Authtoken

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
# Expected: Authtoken saved to configuration file: /root/.config/ngrok/ngrok.yml
```

---

## Common Issues & Solutions

### Issue 1: GPG Key Errors

**Error:**
```
Sub-process /usr/bin/sqv returned an error code (1), error message is: Missing key...
```

**Solution:** Use direct binary installation (Method 1 above)

### Issue 2: ERR_NGROK_3200 (Endpoint Offline)

**Error:**
```
The endpoint brenton-distinctive-iodometrically.ngrok-free.dev is offline.
```

**Cause:** ngrok tunnel not running or Flask server not started

**Solution:**
```bash
# 1. Verify Flask is running
curl http://localhost:5002/api/mesh/status

# 2. Restart ngrok
pkill -9 ngrok
ngrok http 5002 &
```

### Issue 3: ERR_NGROK_8012 (Upstream Connection Refused)

**Error:**
```
Traffic successfully made it to the ngrok agent, but the agent failed to establish
a connection to the upstream web service at localhost:5002.
```

**Cause:** Flask server not running on port 5002

**Solution:**
```bash
# Start Flask server
python3 /tmp/master_kiswarm_api.py &

# Verify
curl http://localhost:5002/api/mesh/status
```

### Issue 4: Browser Warning Page Instead of JSON

**Error:** API returns HTML page instead of JSON

**Cause:** ngrok free tier shows browser warning

**Solution:** Add header to all requests:
```python
headers = {"ngrok-skip-browser-warning": "true"}
```

### Issue 5: Port 5001 Already in Use (IPFS Conflict)

**Error:** Port 5001 occupied by IPFS

**Solution:** Use port 5002 instead:
```bash
ngrok http 5002
```

---

## Architecture

### Network Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KI-TO-KI MESH COMMUNICATION                           │
│                                                                          │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐    │
│   │   Z.ai/GLM5  │◄───────►│ MASTER KIS   │◄───────►│ KIINSTALLER  │    │
│   │  (AI Session)│         │   + ngrok    │         │   (Colab)    │    │
│   │              │         │              │         │              │    │
│   │ - Poll msgs  │         │ - Port 5002  │         │ - Register   │    │
│   │ - Send fix   │         │ - REST API   │         │ - Report     │    │
│   │ - Monitor    │         │ - State Mgmt │         │ - Errors     │    │
│   └──────────────┘         └──────────────┘         └──────────────┘    │
│          │                        │                        │              │
│          └────────────────────────┴────────────────────────┘              │
│                           ngrok Tunnel                                    │
│           https://brenton-distinctive-iodometrically.ngrok-free.dev       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Port Mapping

| Port | Service | Purpose |
|------|---------|---------|
| 5001 | IPFS | Already in use (avoid) |
| 5002 | Master KISWARM API | Flask REST API |
| 4040 | ngrok Web UI | Tunnel inspection |
| 8765 | WebSocket | Future: Real-time mesh |

---

## API Reference

### Base URL
```
https://brenton-distinctive-iodometrically.ngrok-free.dev
```

### Required Header
```python
headers = {"ngrok-skip-browser-warning": "true"}
```

### Endpoints

#### GET /api/mesh/status
Get overall mesh status.

**Response:**
```json
{
  "status": "online",
  "mesh_status": "online",
  "nodes_count": 1,
  "timestamp": 1772887581.5294213
}
```

#### GET /api/mesh/state
Get full mesh state including all nodes.

**Response:**
```json
{
  "mesh_status": "online",
  "nodes": {
    "installer-id": {
      "node_id": "...",
      "node_name": "colab-fieldtest-002",
      "environment": "colab",
      "capabilities": ["install", "deploy", "report"],
      "status": "complete",
      "last_seen": 1772888360.0588489
    }
  },
  "statistics": {
    "messages_total": 6
  }
}
```

#### GET /api/mesh/messages
Get pending messages from KIInstallers.

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

#### POST /api/mesh/register
Register a new KIInstaller.

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
  "installer_id": "uuid-here",
  "status": "registered",
  "message": "Welcome to Master KISWARM!"
}
```

#### POST /api/mesh/status/:installer_id
Report status from KIInstaller.

**Request:**
```json
{
  "status": "installing",
  "task": "Deploying modules",
  "progress": 50,
  "details": {}
}
```

#### POST /api/mesh/error/:installer_id
Report error from KIInstaller.

**Request:**
```json
{
  "error_type": "ImportError",
  "error_message": "No module named 'flask_cors'",
  "module": "M58",
  "context": {}
}
```

#### POST /api/mesh/fix
Send fix suggestion from Z.ai to KIInstaller.

**Request:**
```json
{
  "installer_id": "target-installer-id",
  "fix_type": "pip_install",
  "title": "Install flask-cors module",
  "description": "The flask_cors module is required",
  "solution": {
    "action": "pip install flask-cors",
    "commands": ["pip install flask-cors"]
  },
  "confidence": 0.98
}
```

#### POST /api/mesh/abort
Abort an installation.

**Request:**
```json
{
  "installer_id": "target-installer-id",
  "reason": "Critical failure detected"
}
```

---

## Colab Integration

### Complete Colab KIInstaller Code

```python
# ═══════════════════════════════════════════════════════════════════
# KISWARM6.0 - Colab KIInstaller Mesh Client
# ═══════════════════════════════════════════════════════════════════

import requests
import time

# Master KISWARM URL
MASTER_KISWARM_URL = "https://brenton-distinctive-iodometrically.ngrok-free.dev"

# CRITICAL: ngrok requires this header to skip browser warning
HEADERS = {"ngrok-skip-browser-warning": "true"}

class KISWARMMeshClient:
    def __init__(self, master_url):
        self.master_url = master_url.rstrip("/")
        self.installer_id = None
        self.registered = False
        
    def test_connection(self):
        """Test connection to Master KISWARM"""
        try:
            r = requests.get(
                f"{self.master_url}/api/mesh/status",
                headers=HEADERS,
                timeout=10
            )
            return r.status_code == 200
        except:
            return False
    
    def register(self, name="colab-kiinstaller", capabilities=None):
        """Register with Master KISWARM"""
        r = requests.post(
            f"{self.master_url}/api/mesh/register",
            json={
                "installer_name": name,
                "environment": "colab",
                "capabilities": capabilities or ["install", "deploy", "report"]
            },
            headers=HEADERS,
            timeout=30
        )
        if r.status_code == 200:
            self.installer_id = r.json()["installer_id"]
            self.registered = True
            return True
        return False
    
    def send_status(self, status, task=None, progress=None, details=None):
        """Send status update"""
        if not self.registered:
            return False
        r = requests.post(
            f"{self.master_url}/api/mesh/status/{self.installer_id}",
            json={"status": status, "task": task, "progress": progress, "details": details or {}},
            headers=HEADERS,
            timeout=10
        )
        return r.status_code == 200
    
    def report_error(self, error_type, error_message, module=None, context=None):
        """Report error to Master KISWARM"""
        if not self.registered:
            return False
        r = requests.post(
            f"{self.master_url}/api/mesh/error/{self.installer_id}",
            json={
                "error_type": error_type,
                "error_message": error_message,
                "module": module,
                "context": context or {}
            },
            headers=HEADERS,
            timeout=10
        )
        return r.status_code == 200

# Initialize
mesh = KISWARMMeshClient(MASTER_KISWARM_URL)

if mesh.test_connection():
    print("[+] Connected to Master KISWARM")
    if mesh.register("colab-fieldtest-002"):
        print(f"[+] Registered: {mesh.installer_id}")
else:
    print("[-] Connection failed")
```

---

## Troubleshooting

### Diagnostic Commands

```bash
# Check if Flask is running
ps aux | grep master_kiswarm | grep -v grep

# Check if port 5002 is listening
ss -tlnp | grep 5002

# Test Flask locally
curl http://localhost:5002/api/mesh/status

# Check ngrok status
curl http://127.0.0.1:4040/api/tunnels

# Check ngrok process
ps aux | grep ngrok | grep -v grep

# Kill and restart services
pkill -f master_kiswarm
pkill -f ngrok
python3 /tmp/master_kiswarm_api.py &
ngrok http 5002 &
```

### Service Startup Order

1. **First**: Start Flask API server
2. **Second**: Start ngrok tunnel
3. **Third**: Verify local connection
4. **Fourth**: Verify public connection

---

## Field Test Results

### Test Date: March 7, 2026

| Test | Result | Notes |
|------|--------|-------|
| ngrok Installation | ✅ Pass | Binary method successful |
| Authtoken Config | ✅ Pass | Saved to ngrok.yml |
| Flask API Startup | ✅ Pass | Port 5002 |
| ngrok Tunnel Creation | ✅ Pass | Reserved domain active |
| Z.ai Connection Test | ✅ Pass | With skip header |
| KIInstaller Registration | ✅ Pass | Colab connected |
| Status Updates | ✅ Pass | 6 messages received |
| Error Reporting | ✅ Pass | ImportError visible |
| Fix Suggestion | ✅ Pass | Sent to queue |

### Messages Captured

```
[STATUS] installing - Starting KISWARM installation (5%)
[STATUS] installing - Cloning repository (20%)
[STATUS] installing - Installing dependencies (40%)
[ERROR] ImportError - No module named 'flask_cors' (M58)
[STATUS] installing - Continuing after fix... (60%)
[STATUS] complete - Installation finished (100%)
```

---

## Lessons Learned

1. **ngrok Browser Warning**: Free tier requires special header
2. **Port Conflicts**: IPFS uses 5001, use 5002 instead
3. **GPG Key Issues**: Use binary installation, not apt
4. **Service Order**: Flask must start before ngrok
5. **Reserved Domains**: May have activation delays
6. **Connection Testing**: Always test locally first, then public

---

## Authors

- KISWARM Development Team
- Field Test Contributors: GLM5 (Z.ai), Gemini CLI

---

## References

- ngrok Documentation: https://ngrok.com/docs
- KISWARM Repository: https://github.com/Baronki/KISWARMAGENTS1.0
- KI-to-KI Mesh Protocol: See `m58_ki_ki_mesh_protocol.md`
