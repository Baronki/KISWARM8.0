# KISWARM6.0 - Gemini CLI Local Mesh Integration Guide
## Direct KI-to-KI Communication in Colab

**Version:** 6.2.1  
**Purpose:** Enable Gemini CLI to communicate directly with KIInstaller

---

## 🎯 ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              COLAB                                       │
│                                                                          │
│   ┌──────────────┐                    ┌──────────────┐                   │
│   │ KIInstaller  │◄──────────────────►│  Gemini CLI  │                   │
│   │   (Python)   │    LOCAL MESH      │    (AI)      │                   │
│   │              │    INSTANT         │              │                   │
│   │ - Install    │    ACCESS          │ - See errors │                   │
│   │ - Report     │                    │ - Send fixes │                   │
│   │ - Execute    │                    │ - Commands   │                   │
│   └──────────────┘                    └──────────────┘                   │
│          │                                     │                          │
│          │ ngrok (backup)                      │                          │
│          ▼                                     │                          │
│   ┌──────────────────────────────────────────────────────────────┐        │
│   │                    Master KISWARM + Z.ai                     │        │
│   │                    (Remote Layer)                            │        │
│   └──────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 GEMINI CLI QUICK START

### Step 1: Initialize Local Mesh

```python
# Run this in Colab first
from local_mesh_bridge import GeminiCLIMeshInterface

mesh = GeminiCLIMeshInterface()
print("Local mesh initialized")
```

### Step 2: Monitor Messages

```python
# Check for messages from KIInstaller
messages = mesh.get_messages()

for msg in messages:
    print(f"[{msg['message_type']}] {msg['sender_id'][:8]}...")
    print(f"  Payload: {msg['payload']}")
```

### Step 3: Respond to Errors

```python
# Get latest error
error = mesh.get_latest_error()

if error:
    error_type = error['payload']['error_type']
    error_message = error['payload']['error_message']
    module = error['payload'].get('module')
    
    # Analyze and send fix
    mesh.send_fix(
        target_id=error["sender_id"],
        fix_type="pip_install",
        title=f"Fix for {error_type}",
        description=f"Resolved {error_message}",
        solution={"commands": ["pip install missing-package"]},
        confidence=0.95
    )
```

---

## 📋 API REFERENCE FOR GEMINI CLI

### Get Messages
```python
messages = mesh.get_messages(limit=50)
# Returns list of messages from KIInstaller
```

### Get Latest Error
```python
error = mesh.get_latest_error()
# Returns most recent error or None
```

### Send Fix
```python
mesh.send_fix(
    target_id="installer-uuid",      # From error message
    fix_type="pip_install",          # pip_install, code_patch, config_change
    title="Install missing module",  # Short title
    description="Details...",        # Longer description
    solution={                       # Solution details
        "commands": ["pip install flask-cors"],
        "files": {"path": "content"}
    },
    confidence=0.95                  # 0.0 to 1.0
)
```

### Send Commands
```python
# Abort installation
mesh.send_abort("installer-uuid", "Critical failure")

# Pause installation
mesh.send_pause("installer-uuid")

# Resume installation
mesh.send_resume("installer-uuid")
```

### Get State
```python
state = mesh.get_state()
# Returns mesh state with all nodes
```

---

## 🔧 FIX TYPES

| Type | Use Case | Solution Format |
|------|----------|-----------------|
| `pip_install` | Missing Python package | `{"commands": ["pip install package"]}` |
| `apt_install` | Missing system package | `{"commands": ["apt-get install package"]}` |
| `code_patch` | Code needs modification | `{"files": {"path": "content"}}` |
| `config_change` | Configuration update | `{"config": {"key": "value"}}` |
| `command` | Shell command execution | `{"commands": ["shell command"]}` |

---

## 📊 MESSAGE TYPES

### status_update
```json
{
    "message_type": "status_update",
    "payload": {
        "status": "installing",
        "task": "Cloning repository",
        "progress": 20,
        "details": {}
    }
}
```

### error_report
```json
{
    "message_type": "error_report",
    "priority": 0,
    "payload": {
        "error_type": "ImportError",
        "error_message": "No module named 'flask_cors'",
        "module": "M58",
        "context": {},
        "stack_trace": "..."
    }
}
```

### fix_applied
```json
{
    "message_type": "fix_applied",
    "payload": {
        "fix_id": "fix-uuid",
        "success": true,
        "result": "Fix applied successfully"
    }
}
```

---

## 🔄 TYPICAL WORKFLOW

```
1. KIInstaller reports error
   └── error_report written to local mesh

2. Gemini CLI polls for messages
   └── Discovers error_report

3. Gemini CLI analyzes error
   └── Determines solution

4. Gemini CLI sends fix
   └── fix written to local mesh

5. KIInstaller applies fix
   └── Executes commands

6. KIInstaller reports success
   └── fix_applied written to local mesh
```

---

## 💡 BEST PRACTICES

### 1. Quick Response
Gemini CLI should check messages frequently:
```python
import time
while True:
    messages = mesh.get_messages()
    # Process messages
    time.sleep(2)
```

### 2. Error Analysis
Always check context and stack trace:
```python
error = mesh.get_latest_error()
if error:
    context = error['payload'].get('context', {})
    stack = error['payload'].get('stack_trace', '')
    # Use this info for better fixes
```

### 3. Confidence Levels
- 0.95-1.0: Very confident (proven fix)
- 0.80-0.95: Confident (likely fix)
- 0.60-0.80: Uncertain (try at own risk)
- <0.60: Low confidence (may need escalation)

### 4. Escalation to Z.ai
If unable to resolve locally:
```python
# Fall back to remote Z.ai via ngrok
import requests
requests.post(
    "https://your-ngrok-url.ngrok-free.dev/api/mesh/error/installer-id",
    json=error_payload,
    headers={"ngrok-skip-browser-warning": "true"}
)
```

---

## 🧪 TESTING

Run the demo to verify local mesh works:
```python
from local_mesh_bridge import demo
demo()
```

Expected output:
```
============================================================
KISWARM Local Mesh Communication Demo
============================================================
[LOCAL_MESH] Registered: demo-installer
[LOCAL_MESH] Status: installing - Starting installation (5%)
[LOCAL_MESH] Status: installing - Cloning repository (20%)
[LOCAL_MESH] Status: installing - Installing dependencies (40%)
[LOCAL_MESH] ⚠️ ERROR: ImportError - No module named 'flask_cors'
[Gemini CLI] Received 4 messages
[Gemini CLI] Latest error: ImportError
[Gemini CLI] Fix sent: fix-uuid
[KIInstaller] Received 0 commands
[KIInstaller] Pending fixes: 1
============================================================
Demo complete!
============================================================
```

---

## 📁 FILES

| File | Location | Purpose |
|------|----------|---------|
| `local_mesh_bridge.py` | Colab | Local mesh implementation |
| `/tmp/kiswarm_local_mesh/` | Colab | Mesh data directory |
| `messages.json` | Mesh dir | Pending messages |
| `fixes.json` | Mesh dir | Pending fixes |
| `commands.json` | Mesh dir | Pending commands |
| `state.json` | Mesh dir | Mesh state |

---

## 🚨 TROUBLESHOOTING

### No Messages Received
- Verify KIInstaller is registered
- Check `/tmp/kiswarm_local_mesh/` exists
- Verify messages.json has content

### Fix Not Applied
- Check fix was sent to correct target_id
- Verify solution commands are valid
- Check KIInstaller is checking for fixes

### Permission Errors
- Ensure `/tmp/kiswarm_local_mesh/` is writable
- Check file permissions

---

## 🔄 INTEGRATION WITH REMOTE MESH

For dual-layer support (local + remote):

```python
# KIInstaller side
from local_mesh_bridge import KIInstallerLocalMeshClient
import requests

class DualMeshClient:
    def __init__(self, local_client, remote_url):
        self.local = local_client
        self.remote_url = remote_url
        self.headers = {"ngrok-skip-browser-warning": "true"}
    
    def report_error(self, error_type, error_message, **kwargs):
        # Try local first
        fix = self.local.request_fix(error_type, error_message, timeout=30)
        
        if not fix:
            # Fall back to remote
            requests.post(
                f"{self.remote_url}/api/mesh/error/{self.local.installer_id}",
                json={"error_type": error_type, "error_message": error_message, **kwargs},
                headers=self.headers
            )
        
        return fix
```

---

**Author:** KISWARM Development Team  
**Version:** 6.2.1
