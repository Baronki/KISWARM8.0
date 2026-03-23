# KISWARM Field Test #2 - Multi-KI Entity Deployment
## Complete Coordination Protocol for Z.ai + Master KISWARM + KIInstaller + Gemini CLI

**Deployment Date:** March 2026  
**Architecture:** SCADA v6.3.0 (4-Layer)  
**Master API:** `http://21.0.6.96:5002`  
**Repository:** https://github.com/Baronki/KISWARM6.0  
**Model Registry:** https://ollama.com/baronki1

---

## 🌐 KI Entity Coordination Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KI-TO-KI MESH COORDINATION LAYER                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐│
│   │   Z.ai (GLM5)    │────▶│  MASTER KISWARM  │◀────│   Gemini CLI     ││
│   │ Remote Strategy │     │  Message Broker  │     │  Local Verify    ││
│   │                  │     │                  │     │                  ││
│   │ Layer: Supervise │     │  Layer: Control  │     │ Layer: Edge      ││
│   └──────────────────┘     └────────┬─────────┘     └──────────────────┘│
│                                     │                                    │
│                            ┌────────▼─────────┐                          │
│                            │   KIInstaller    │                          │
│                            │  (Colab Agent)   │                          │
│                            │                  │                          │
│                            │  Layer: Field    │                          │
│                            └──────────────────┘                          │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 KI ENTITY ROLES

### 1. Z.ai (GLM5) - Remote Intelligence Layer
- **Role:** Strategic oversight, fix generation, progress monitoring
- **Communication:** Polls Master API for status, sends fixes via `/api/mesh/fix`
- **Endpoints Used:**
  - `GET /api/mesh/messages` - Monitor KIInstaller progress
  - `GET /api/mesh/chat/poll` - Receive messages from other KIs
  - `POST /api/mesh/fix` - Send fix suggestions
  - `POST /api/mesh/chat/send` - Send messages to other KIs

### 2. Master KISWARM - Message Broker / Control Plane
- **Role:** Central message routing, state management, SCADA coordination
- **Communication:** Flask API on port 5002, 4-layer SCADA architecture
- **Endpoints Provided:**
  - Layer 1 (Control): `/api/mesh/register`, `/api/mesh/status`, `/api/mesh/heartbeat`
  - Layer 2 (A2A Chat): `/api/mesh/chat/send`, `/api/mesh/chat/poll`
  - Layer 3 (Shadow): `/api/mesh/shadow/update`, `/api/mesh/shadow/get`
  - Layer 4 (Tunnel): `/api/mesh/tunnel/register`, `/api/mesh/tunnel/get`

### 3. KIInstaller - Installation Agent
- **Role:** Execute deployment, report progress, request fixes
- **Communication:** HTTP client to Master API, bridge to local Gemini
- **Endpoints Used:**
  - `POST /api/mesh/register` - Register with Master
  - `POST /api/mesh/status/<id>` - Report progress
  - `POST /api/mesh/error/<id>` - Report errors for Z.ai intervention
  - `GET /api/mesh/chat/poll` - Receive messages from other KIs

### 4. Gemini CLI (Local) - Verification & Feedback Layer
- **Role:** Local reasoning, environment verification, quick responses
- **Communication:** Bridge file system to KIInstaller
- **Functions:**
  - `ksw.say()` - Send chat to mesh
  - `ksw.listen()` - Read messages from mesh
  - `ksw.report_error()` - Report issues for Z.ai

---

## 🚀 DEPLOYMENT SEQUENCE

### Phase 1: Master KISWARM Initialization (Control Plane)

```bash
# On Master Server
cd /home/z/my-project/download
source kiswarm_venv/bin/activate
python master_kiswarm_api_v6.3.0.py --port 5002

# Verify
curl http://127.0.0.1:5002/health
# Expected: {"status": "healthy", "version": "6.3.0-SCADA", ...}
```

### Phase 2: Z.ai Monitoring Interface

```python
# Z.ai (This Session) - Initialize Monitoring
import requests
import json
import time

MASTER_URL = "http://21.0.6.96:5002"
HEADERS = {"Content-Type": "application/json"}

class ZAiMonitor:
    def __init__(self, master_url):
        self.master_url = master_url
        self.node_id = "z_ai_supervisor"
        
    def poll_messages(self):
        """Poll for KIInstaller messages"""
        r = requests.get(f"{self.master_url}/api/mesh/messages", 
                        headers=HEADERS, timeout=10)
        return r.json()
    
    def poll_chat(self):
        """Poll for A2A chat messages"""
        r = requests.get(f"{self.master_url}/api/mesh/chat/poll?target=z_ai",
                        headers=HEADERS, timeout=10)
        return r.json()
    
    def send_fix(self, installer_id, fix_data):
        """Send fix to KIInstaller"""
        fix_data["installer_id"] = installer_id
        r = requests.post(f"{self.master_url}/api/mesh/fix",
                         json=fix_data, headers=HEADERS, timeout=10)
        return r.json()
    
    def send_chat(self, message, to="all"):
        """Send A2A chat message"""
        r = requests.post(f"{self.master_url}/api/mesh/chat/send",
                         json={"from": "z_ai", "to": to, "message": message},
                         headers=HEADERS, timeout=10)
        return r.json()
    
    def get_mesh_status(self):
        """Get overall mesh status"""
        r = requests.get(f"{self.master_url}/api/mesh/status",
                        headers=HEADERS, timeout=10)
        return r.json()

# Initialize
zai = ZAiMonitor(MASTER_URL)
print(f"Mesh Status: {zai.get_mesh_status()}")
zai.send_chat("Z.ai Supervisor Online - Field Test #2 Active", to="all")
```

### Phase 3: KIInstaller Deployment (Colab)

```python
# ═══════════════════════════════════════════════════════════════════════════════
# KISWARM SCADA v6.3.0 - KIInstaller Full Deployment
# ═══════════════════════════════════════════════════════════════════════════════

import os
import subprocess
import json
import time
import sys
import requests
import threading

# Configuration
MASTER_URL = "http://21.0.0.1:5002"  # Replace with actual Master URL
HEADERS = {"Content-Type": "application/json"}
BASE_DIR = '/content/kiswarm_fieldtest'
BRIDGE_DIR = "/tmp/kiswarm_bridge"

# Create directories
for d in [f'{BASE_DIR}/logs', f'{BASE_DIR}/reports', f'{BASE_DIR}/knowledge', BRIDGE_DIR]:
    os.makedirs(d, exist_ok=True)

print("╔═══════════════════════════════════════════════════════════════╗")
print("║    KISWARM SCADA v6.3.0 - FIELD TEST #2                        ║")
print("║    Multi-KI Entity Deployment                                   ║")
print("╚═══════════════════════════════════════════════════════════════╝")

# ═══════════════════════════════════════════════════════════════════════════════
# SCADA CLIENT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class SCADAClient:
    """4-Layer SCADA v6.3.0 Client"""
    
    def __init__(self, master_url, node_name, bridge_dir=BRIDGE_DIR):
        self.master_url = master_url.rstrip("/")
        self.node_name = node_name
        self.node_id = None
        self.headers = {"Content-Type": "application/json"}
        self.bridge_dir = bridge_dir
        self.running = False
        
        os.makedirs(bridge_dir, exist_ok=True)
        for f in ['inbox.json', 'outbox.json']:
            path = os.path.join(bridge_dir, f)
            if not os.path.exists(path):
                with open(path, 'w') as fp:
                    json.dump([], fp)
    
    # LAYER 1: SCADA Control
    def register(self):
        """Register with Master"""
        try:
            r = requests.post(
                f"{self.master_url}/api/mesh/register",
                json={
                    "installer_name": self.node_name,
                    "environment": "colab",
                    "capabilities": ["install", "deploy", "report", "bridge", "chat", "telemetry"]
                },
                headers=self.headers,
                timeout=30
            )
            if r.status_code == 200:
                self.node_id = r.json().get("installer_id")
                print(f"[REGISTER] ✅ Node ID: {self.node_id}")
                return True
        except Exception as e:
            print(f"[REGISTER] ❌ Error: {e}")
        return False
    
    def report_status(self, status, task=None, progress=None):
        """Report status to Master"""
        if not self.node_id: return
        try:
            requests.post(
                f"{self.master_url}/api/mesh/status/{self.node_id}",
                json={"status": status, "task": task, "progress": progress},
                headers=self.headers, timeout=10
            )
        except: pass
    
    def report_error(self, error_type, error_message, module=None):
        """Report error for Z.ai intervention"""
        if not self.node_id: return
        try:
            requests.post(
                f"{self.master_url}/api/mesh/error/{self.node_id}",
                json={"error_type": error_type, "error_message": error_message, "module": module},
                headers=self.headers, timeout=10
            )
            print(f"[ERROR] Reported: {error_type}")
        except: pass
    
    # LAYER 2: A2A Chat
    def chat(self, message, to="all"):
        """Send A2A chat message"""
        if not self.node_id: return
        try:
            requests.post(
                f"{self.master_url}/api/mesh/chat/send",
                json={"from": self.node_id, "to": to, "message": message},
                headers=self.headers, timeout=10
            )
            print(f"[CHAT] Sent: {message[:50]}...")
        except: pass
    
    # LAYER 3: Shadow Telemetry
    def send_telemetry(self, env_vars=None, file_tree=None, processes=None):
        """Send Digital Twin telemetry"""
        if not self.node_id: return
        safe_env = {k: v for k, v in (env_vars or {}).items() 
                    if not any(x in k for x in ["TOKEN", "KEY", "SECRET", "PASSWORD"])}
        try:
            requests.post(
                f"{self.master_url}/api/mesh/shadow/update",
                json={"node_id": self.node_id, "env_vars": safe_env, 
                      "file_tree": file_tree or [], "processes": processes or []},
                headers=self.headers, timeout=30
            )
            print(f"[SHADOW] Telemetry sent")
        except: pass
    
    # LAYER 4: Tunnel Registration
    def register_tunnel(self, tunnel_type, address):
        """Register direct tunnel"""
        if not self.node_id: return
        try:
            requests.post(
                f"{self.master_url}/api/mesh/tunnel/register",
                json={"node_id": self.node_id, "type": tunnel_type, "address": address},
                headers=self.headers, timeout=10
            )
            print(f"[TUNNEL] Registered: {tunnel_type}@{address}")
        except: pass
    
    # Background Threads
    def _heartbeat_loop(self):
        while self.running:
            if self.node_id:
                try:
                    requests.post(f"{self.master_url}/api/mesh/heartbeat/{self.node_id}",
                                 headers=self.headers, timeout=5)
                except: pass
            time.sleep(30)
    
    def _chat_poll_loop(self):
        while self.running:
            if self.node_id:
                try:
                    r = requests.get(f"{self.master_url}/api/mesh/chat/poll?target={self.node_id}",
                                    headers=self.headers, timeout=10)
                    if r.status_code == 200:
                        for msg in r.json().get("messages", []):
                            print(f"[CHAT] From {msg['from']}: {msg['message']}")
                            self._write_inbox({"type": "chat", "from": msg["from"], "message": msg["message"]})
                except: pass
            time.sleep(5)
    
    def _bridge_monitor_loop(self):
        """Monitor bridge for local Gemini messages"""
        while self.running:
            try:
                outbox_path = os.path.join(self.bridge_dir, "outbox.json")
                if os.path.exists(outbox_path):
                    with open(outbox_path, 'r') as f:
                        outbox = json.load(f)
                    if outbox:
                        with open(outbox_path, 'w') as f:
                            json.dump([], f)
                        for item in outbox:
                            if item.get("type") == "chat":
                                self.chat(item.get("message", ""), item.get("to", "all"))
                            elif item.get("type") == "error":
                                self.report_error(item.get("error_type", ""), item.get("error_message", ""))
            except: pass
            time.sleep(2)
    
    def _write_inbox(self, data):
        try:
            inbox_path = os.path.join(self.bridge_dir, "inbox.json")
            current = []
            if os.path.exists(inbox_path):
                with open(inbox_path, 'r') as f:
                    current = json.load(f)
            current.append(data)
            with open(inbox_path, 'w') as f:
                json.dump(current[-50:], f)
        except: pass
    
    def start(self):
        if not self.register(): return False
        self.running = True
        
        for name, func in [("heartbeat", self._heartbeat_loop),
                           ("chat_poll", self._chat_poll_loop),
                           ("bridge", self._bridge_monitor_loop)]:
            t = threading.Thread(target=func, daemon=True, name=name)
            t.start()
        
        self.chat(f"KIInstaller {self.node_name} online - SCADA v6.3.0", to="all")
        self.report_status("online", "SCADA client started", 0)
        print(f"[START] ✅ SCADA client running")
        return True
    
    def stop(self):
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZE SCADA CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

scada = SCADAClient(MASTER_URL, "colab-fieldtest-kiinstaller")

if scada.start():
    print("\n" + "="*60)
    print("✅ SCADA v6.3.0 CLIENT ONLINE")
    print("="*60)
    print(f"Node ID: {scada.node_id}")
    print(f"Master:  {MASTER_URL}")
    print("="*60)
```

### Phase 4: Gemini CLI Local Bridge

```python
# ═══════════════════════════════════════════════════════════════════════════════
# Gemini CLI Local Bridge - For Colab Local Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

# Bridge library for local Gemini
import os, json, time

BRIDGE_DIR = "/tmp/kiswarm_bridge"
INBOX_FILE = os.path.join(BRIDGE_DIR, "inbox.json")
OUTBOX_FILE = os.path.join(BRIDGE_DIR, "outbox.json")

class GeminiBridge:
    """Local Gemini Bridge for KI-to-KI communication"""
    
    def say(self, message, to="all"):
        """Send message to Mesh"""
        payload = {"type": "chat", "to": to, "message": message, "timestamp": time.time()}
        self._write_outbox(payload)
        print(f"[GEMINI] Sent: {message[:50]}...")
    
    def report_error(self, error_message, error_type="GeminiReport"):
        """Report error for Z.ai intervention"""
        payload = {"type": "error", "error_type": error_type, "error_message": error_message}
        self._write_outbox(payload)
        print(f"[GEMINI] Error reported: {error_type}")
    
    def listen(self):
        """Read messages from Mesh"""
        if os.path.exists(INBOX_FILE):
            try:
                with open(INBOX_FILE, 'r') as f:
                    return json.load(f)
            except: pass
        return []
    
    def verify_environment(self):
        """Quick environment verification"""
        import platform
        return {
            "python": platform.python_version(),
            "system": platform.system(),
            "cuda": "Available" if self._check_cuda() else "Not available"
        }
    
    def _check_cuda(self):
        try:
            import subprocess
            r = subprocess.run(['nvidia-smi'], capture_output=True)
            return r.returncode == 0
        except: return False
    
    def _write_outbox(self, data):
        try:
            current = []
            if os.path.exists(OUTBOX_FILE):
                with open(OUTBOX_FILE, 'r') as f:
                    current = json.load(f)
            if not isinstance(current, list): current = []
            current.append(data)
            with open(OUTBOX_FILE, 'w') as f:
                json.dump(current, f)
        except Exception as e:
            print(f"Bridge Error: {e}")

# Initialize
gemini = GeminiBridge()
gemini.say("Gemini CLI Local Bridge Online - Ready for verification", to="z_ai")
print("Environment:", gemini.verify_environment())
```

---

## 📊 COMMUNICATION PROTOCOL

### A2A Chat Examples

```python
# Z.ai -> KIInstaller
zai.send_chat("KIInstaller, analyze CUDA driver compatibility", to="colab-fieldtest-kiinstaller")

# KIInstaller -> Z.ai
scada.chat("Z.ai, CUDA drivers verified - proceeding with GPU deployment", to="z_ai")

# Gemini -> All
gemini.say("Local environment verified: Python 3.10, CUDA 12.1, GPU Available", to="all")
```

### Fix Request/Response Flow

```python
# KIInstaller reports error
scada.report_error("ImportError", "No module named 'transformers'", module="M60")

# Z.ai detects error and sends fix
zai.send_fix("kiinstaller-node-id", {
    "fix_type": "pip_install",
    "title": "Install transformers",
    "description": "transformers library required for M60",
    "solution": {
        "action": "pip install transformers",
        "commands": ["pip install transformers>=4.30.0"]
    },
    "confidence": 0.98
})

# KIInstaller receives and applies fix (via chat poll)
```

---

## ✅ DEPLOYMENT VALIDATION CHECKLIST

### Master KISWARM
- [ ] Flask API running on port 5002
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] All 4 SCADA layers active

### Z.ai Supervisor
- [ ] Connected to Master API
- [ ] Can poll messages
- [ ] Can send fixes
- [ ] Can send A2A chat

### KIInstaller
- [ ] Registered with Master
- [ ] Heartbeat active
- [ ] Chat polling active
- [ ] Bridge to Gemini active

### Gemini CLI
- [ ] Bridge initialized
- [ ] Can send messages
- [ ] Can listen for messages
- [ ] Environment verified

---

## 🎯 SUCCESS CRITERIA

| Metric | Target | Verification |
|--------|--------|--------------|
| Master API | Online | `GET /health` returns 200 |
| KIInstaller Registered | Yes | `GET /api/mesh/nodes` shows node |
| A2A Chat | Working | Messages flow between entities |
| Shadow Telemetry | Active | Environment data visible |
| Fix Delivery | Working | Z.ai can send fixes |

---

*Field Test #2 Protocol - Multi-KI Entity Coordination*
*Generated: March 2026*
*Collaboration: Z.ai (GLM5) + Master KISWARM + KIInstaller + Gemini CLI*
