# KISWARM6.0 - Field Test #2 Preparation Guide
## Master KISWARM Deployment with ngrok

---

## 🎯 OVERVIEW

This guide prepares you for Field Test #2 with:
- **Master KISWARM** running locally and exposed via ngrok
- **KIInstaller** in Colab connecting to Master via ngrok tunnel
- **Z.ai** (this session) monitoring and intervening via REST API

---

## 📋 ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KI-TO-KI MESH LAYER                              │
│                                                                          │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐          │
│   │   Z.ai (ME)  │─────▶│ MASTER KIS   │◀─────│ KIINSTALLER  │          │
│   │  (This Env)  │      │   + ngrok    │      │   (Colab)    │          │
│   │              │      │              │      │              │          │
│   │  ┌────────┐  │      │  ┌────────┐  │      │  ┌────────┐  │          │
│   │  │REST API│  │      │  │PUBLIC  │  │      │  │ MESH   │  │          │
│   │  │POLL    │  │      │  │ URL    │  │      │  │ CLIENT │  │          │
│   │  └────────┘  │      │  └────────┘  │      │  └────────┘  │          │
│   └──────────────┘      └──────────────┘      └──────────────┘          │
│         │                     │                     │                    │
│         │    ┌────────────────┴────────────────┐    │                    │
│         │    │         ngrok tunnel            │    │                    │
│         │    │   https://xxx.ngrok-free.app    │    │                    │
│         │    └────────────────┬────────────────┘    │                    │
│         │                     │                     │                    │
│         └─────────────────────┴─────────────────────┘                    │
│                     BIDIRECTIONAL COMMUNICATION                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 QUICK START (Recommended)

### Option A: Automated Deployment

Run this single command in your terminal:

```bash
cd /home/z/my-project/KISWARM6.0/backend/python/kibank
bash deploy_master_kiswarm.sh
```

This will:
1. Install all dependencies
2. Install and configure ngrok
3. Start the Master API server
4. Create the ngrok tunnel
5. Output the public URL

---

### Option B: Manual Step-by-Step

Follow these steps in order:

#### STEP 1: Install ngrok

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok
```

#### STEP 2: Add Authtoken

```bash
ngrok config add-authtoken 3Ac51HC51vmerRvn9CodFhxgnYN_771JYNNWUuwi4uQyucxHx
```

#### STEP 3: Install Python Dependencies

```bash
pip install flask flask-cors websockets requests
```

#### STEP 4: Start Master API Server (Terminal 1)

```bash
cd /home/z/my-project/KISWARM6.0/backend/python/kibank
python master_api_server.py --port 5001 --host 0.0.0.0
```

#### STEP 5: Create ngrok Tunnel (Terminal 2)

```bash
ngrok http 5001
```

#### STEP 6: Copy the Public URL

Look for the "Forwarding" line in ngrok output:
```
Forwarding    https://xxxx-xxxx.ngrok-free.app -> http://localhost:5001
```

Copy the `https://...` URL - this is your Master KISWARM public URL!

---

## 📋 TESTING THE SETUP

### Test 1: Local API Check

```bash
curl http://localhost:5001/api/mesh/status
```

Expected:
```json
{"status": "online", "mesh_status": "initializing", ...}
```

### Test 2: ngrok Tunnel Check

```bash
curl https://YOUR-NGROK-URL.ngrok-free.app/api/mesh/status
```

Expected: Same JSON response

### Test 3: ngrok Dashboard

Open in browser: http://127.0.0.1:4040

This shows all traffic flowing through your tunnel.

---

## 📋 FOR COLAB (Field Test #2)

### Updated Colab Notebook Code

Add this to your Colab notebook to connect to Master KISWARM:

```python
# ═══════════════════════════════════════════════════════════════════
# KISWARM6.0 - KIInstaller Mesh Connection
# ═══════════════════════════════════════════════════════════════════

import requests
import time

# REPLACE THIS WITH YOUR NGROK URL FROM STEP 6
MASTER_KISWARM_URL = "https://YOUR-NGROK-URL.ngrok-free.app"

# Test connection
print("[*] Testing connection to Master KISWARM...")
try:
    response = requests.get(f"{MASTER_KISWARM_URL}/api/mesh/status", timeout=10)
    print(f"[+] Connected! Status: {response.json()['status']}")
except Exception as e:
    print(f"[-] Connection failed: {e}")
    raise

# Register KIInstaller
print("[*] Registering KIInstaller...")
response = requests.post(
    f"{MASTER_KISWARM_URL}/api/mesh/register",
    json={
        "installer_name": "colab-fieldtest-002",
        "environment": "colab",
        "capabilities": ["install", "deploy", "report", "test"]
    },
    timeout=30
)

if response.status_code == 200:
    installer_id = response.json()["installer_id"]
    print(f"[+] Registered! ID: {installer_id}")
else:
    print(f"[-] Registration failed")
    raise Exception("Registration failed")

# Report status during installation
def report_status(status, task, progress=None, details=None):
    """Report status to Master KISWARM"""
    requests.post(
        f"{MASTER_KISWARM_URL}/api/mesh/status/{installer_id}",
        json={
            "status": status,
            "task": task,
            "progress": progress,
            "details": details or {}
        },
        timeout=10
    )
    print(f"[*] Status: {status} - {task} ({progress or 0}%)")

# Report error and wait for fix
def report_error(error_type, error_message, module=None, context=None):
    """Report error to Master KISWARM - Z.ai will see this!"""
    print(f"[!] Reporting error: {error_type}")
    requests.post(
        f"{MASTER_KISWARM_URL}/api/mesh/error/{installer_id}",
        json={
            "error_type": error_type,
            "error_message": error_message,
            "module": module,
            "context": context or {}
        },
        timeout=10
    )
    print("[*] Error reported to Z.ai via Master KISWARM")

# Example usage during installation:
# report_status("installing", "Cloning KISWARM repository", 10)
# report_status("installing", "Installing Python dependencies", 30)
# report_status("installing", "Deploying modules", 50)
# report_error("ImportError", "No module named 'flask_cors'", "M58")
# report_status("complete", "Installation finished", 100)
```

---

## 📋 Z.ai MONITORING (From This Session)

Once the Master KISWARM is running, I can monitor and intervene:

### Poll for Messages
```python
import requests

# Poll for messages from KIInstaller
response = requests.get("https://YOUR-NGROK-URL.ngrok-free.app/api/mesh/messages")
messages = response.json()["messages"]

for msg in messages:
    print(f"From {msg['sender_id']}: {msg['payload']}")
```

### Send Fix Suggestion
```python
# Send fix to KIInstaller
response = requests.post(
    "https://YOUR-NGROK-URL.ngrok-free.app/api/mesh/fix",
    json={
        "installer_id": "INSTALLER_ID_FROM_MESSAGE",
        "fix_type": "pip_install",
        "title": "Install flask-cors",
        "description": "Install the missing flask-cors module",
        "solution": {
            "action": "pip install flask-cors",
            "commands": ["pip install flask-cors"]
        },
        "confidence": 0.95
    }
)
```

### Abort Installation
```python
# Abort if critical failure detected
response = requests.post(
    "https://YOUR-NGROK-URL.ngrok-free.app/api/mesh/abort",
    json={
        "installer_id": "INSTALLER_ID",
        "reason": "Critical security vulnerability detected"
    }
)
```

---

## 📋 TROUBLESHOOTING

### ngrok Shows "Online" but API Not Accessible
- Check if Flask server is running: `curl http://localhost:5001/api/mesh/status`
- Check ngrok logs: http://127.0.0.1:4040

### "Connection Refused" in Colab
- Make sure ngrok is running in terminal
- Check the URL is correct (https://... not http://)
- Free tier may have rate limits - wait a minute and retry

### "Tunnel Not Found"
- ngrok free tier tunnels expire after 2 hours of inactivity
- Restart ngrok to get a new URL

---

## 📋 CHECKLIST FOR FIELD TEST #2

Before starting Field Test #2:

- [ ] ngrok installed and configured
- [ ] Master API server running on port 5001
- [ ] ngrok tunnel created and public URL obtained
- [ ] Tested public URL with curl
- [ ] Updated Colab notebook with new Master URL
- [ ] Ready to monitor from Z.ai session

---

## 📋 NEXT STEPS

1. **Now**: Run `bash deploy_master_kiswarm.sh` or follow manual steps
2. **After setup**: Confirm you have the public ngrok URL
3. **Field Test #2**: Run the updated Colab notebook
4. **Monitor**: I'll watch for errors and send fixes in real-time

---

**Status**: Ready for deployment  
**Author**: KISWARM Development Team  
**Version**: 6.2.0
