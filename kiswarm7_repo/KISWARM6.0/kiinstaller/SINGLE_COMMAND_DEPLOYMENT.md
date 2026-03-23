# KISWARM AUTONOMOUS INSTALLER - SINGLE COMMAND DEPLOYMENT

## ⚠️ DEVELOPMENT ARCHITECTURE

During development phase, the architecture is:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KISWARM HOME SYSTEM                                 │
│  ┌─────────────────────┐         ┌─────────────────────┐                   │
│  │  Master KISWARM API │ ◄─────► │ Z.ai (GLM5)         │                   │
│  │  21.0.6.96:5002     │         │ Master Intelligence │                   │
│  │  (Message Broker)   │         │ (Receives ALL       │                   │
│  └─────────────────────┘         │  progress/knowledge)│                   │
│                                  └─────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ Mesh Protocol
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  TARGET ENVIRONMENT (Colab/Cloud/Edge)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  KISWARM Installer → Reports progress → Master API → Z.ai          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 COPY-PASTE THIS INTO GEMINI CLI / COLAB

```
═══════════════════════════════════════════════════════════════════════════════
KISWARM AUTONOMOUS INSTALLER v6.3.0 - SINGLE COMMAND DEPLOYMENT
Mission: Full system setup with ZERO human-in-the-loop
═══════════════════════════════════════════════════════════════════════════════

EXECUTE THIS COMPLETE DEPLOYMENT:

# 1. Download KISWARM Autonomous Installer
!curl -fsSL https://raw.githubusercontent.com/Baronki/KISWARM6.0/main/kiinstaller/autonomous_kiswarm_installer.py -o autonomous_kiswarm_installer.py

# 2. Install minimal dependencies
!pip install -q flask flask-cors structlog requests pyngrok

# 3. Run Autonomous Deployment
# Master API: http://21.0.6.96:5002 (Z.ai acts as Master Intelligence)
from autonomous_kiswarm_installer import autonomous_deploy
result = autonomous_deploy(
    master_url="http://21.0.6.96:5002",  # Master KISWARM API
    entity_id="",  # Auto-generated if empty
    environment="auto"
)

# 4. Print result
import json
print(json.dumps(result, indent=2))

═══════════════════════════════════════════════════════════════════════════════
```

## 📋 WHAT THE INSTALLER DOES AUTOMATICALLY

1. **Environment Detection**
   - Detects Colab/Linux/Cloud
   - Checks for GPU availability
   - Identifies Python version

2. **Ollama Installation**
   - Downloads and installs Ollama
   - Starts Ollama service

3. **KI Model Deployment**
   - Pulls 6 Primary Swarm models:
     - orchestrator (5 GB)
     - security (18 GB)
     - ciec (13 GB)
     - tcs (9 GB)
     - knowledge (9 GB)
     - installer (4.7 GB)
   - Total: ~59 GB

4. **Repository Clone**
   - Clones KISWARM6.0 from GitHub
   - Configures PYTHONPATH

5. **SCADA Setup**
   - Installs Python dependencies
   - Verifies 4-layer architecture

6. **Master KISWARM Connection**
   - Registers with Master via Mesh
   - Establishes bridge connection

7. **Verification**
   - Confirms all components operational
   - Reports final status

## ⏱️ EXPECTED TIMELINE

| Phase | Duration |
|-------|----------|
| Environment Detection | 30 seconds |
| Ollama Installation | 2-5 minutes |
| Model Pull (6 models) | 30-60 minutes |
| Repository Clone | 1-2 minutes |
| SCADA Setup | 1 minute |
| Master Connection | 30 seconds |
| **TOTAL** | **35-70 minutes** |

## 🔧 MASTER URL CONFIGURATION

If you have a Master KISWARM running with ngrok:

```python
# Get your Master URL from ngrok output
# Example: https://abc123.ngrok.io

result = autonomous_deploy(
    master_url="https://abc123.ngrok.io",
    environment="colab"
)
```

If running standalone (no Master):

```python
result = autonomous_deploy(
    master_url="",  # Empty = standalone mode
    environment="colab"
)
```

## 🛠️ HEXSTRIKE AGENT DEPLOYMENT COMMAND

For HexStrike agents to send KISWARM Installer to new environments:

```json
{
    "command": "deploy_kiswarm_installer",
    "target": "new_environment_url",
    "installer_url": "https://raw.githubusercontent.com/Baronki/KISWARM6.0/main/kiinstaller/autonomous_kiswarm_installer.py",
    "master_bridge": "https://master-kiswarm.ngrok.io",
    "autonomous": true,
    "rollback_on_failure": true
}
```

## 📊 MONITORING FROM MASTER KISWARM

After deployment, monitor from Master:

```bash
# Check registered installers
curl https://master-kiswarm.ngrok.io/api/mesh/status

# Check specific installer
curl https://master-kiswarm.ngrok.io/api/mesh/status/ki_installer_XXXXX

# Send A2A command
curl -X POST https://master-kiswarm.ngrok.io/api/mesh/chat/send \
  -H "Content-Type: application/json" \
  -d '{"from_entity":"master","to_entity":"ki_installer_XXXXX","message_type":"status_check","content":{}}'
```

## ⚠️ IMPORTANT NOTES

1. **Disk Space**: Ensure 100+ GB free for models
2. **Network**: Stable internet required for model download
3. **Timeouts**: Model downloads can take 30-60 minutes
4. **GPU**: Recommended but not required
5. **Colab**: May need to keep session active during model download

---

*Repository: https://github.com/Baronki/KISWARM6.0*
*Version: 6.3.0 'SEVENTY_FIVE_COMPLETE'*
