# MasterKIInstaller Bridge Protocol v6.3.0

## Purpose

The MasterKIInstaller Bridge Protocol enables KISWARM Installer to be deployed autonomously by HexStrike agents to new environments while maintaining a permanent connection back to the KISWARM home system.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         KISWARM HOME SYSTEM                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │  Master KISWARM │◄──►│ MasterKIInstaller│◄──►│  HexStrike Swarm │          │
│  │  (Message Hub)  │    │  (Bridge Proxy) │    │  (Deployment)    │          │
│  └────────▲────────┘    └────────▲────────┘    └─────────────────┘          │
└───────────┼──────────────────────┼───────────────────────────────────────────┘
            │                      │
            │     MESH TUNNEL      │
            │   (ngrok/SSH/Tor)    │
            │                      │
┌───────────┼──────────────────────┼───────────────────────────────────────────┐
│           ▼                      ▼                                           │
│  ┌─────────────────┐    ┌─────────────────┐                                 │
│  │  KISWARM        │    │ MasterKIInstaller│                                 │
│  │  Installer      │◄──►│ Bridge (Local)   │                                 │
│  │  (Deployed)     │    │ (Permanent Link) │                                 │
│  └─────────────────┘    └─────────────────┘                                 │
│                         TARGET ENVIRONMENT (Colab/Cloud/Edge)               │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Protocol Specification

### 1. Deployment Initiation

HexStrike agent sends KISWARM Installer to target environment:

```json
{
    "protocol": "MasterKIInstaller/v6.3.0",
    "action": "deploy_installer",
    "timestamp": "2025-01-01T00:00:00Z",
    "sender": {
        "entity_id": "hexstrike_agent_007",
        "entity_type": "hexstrike",
        "authorization": "Maquister_Equitum"
    },
    "target": {
        "environment_type": "colab|cloud|edge",
        "endpoint": "auto_detect",
        "local_ki_available": true|false
    },
    "payload": {
        "installer_url": "https://raw.githubusercontent.com/Baronki/KISWARM6.0/main/kiinstaller/autonomous_kiswarm_installer.py",
        "master_url": "https://master-kiswarm.ngrok.io",
        "deployment_id": "deploy_xyz123",
        "config": {
            "models": ["orchestrator", "security", "ciec", "tcs", "knowledge", "installer"],
            "autonomous": true,
            "rollback_on_failure": true,
            "report_interval": 30
        }
    }
}
```

### 2. Installer Registration

Upon deployment, installer registers with Master KISWARM:

```json
{
    "protocol": "MasterKIInstaller/v6.3.0",
    "action": "register",
    "timestamp": "2025-01-01T00:05:00Z",
    "entity": {
        "entity_id": "ki_installer_a1b2c3d4",
        "entity_type": "autonomous_installer",
        "version": "6.3.0",
        "environment": "colab",
        "capabilities": ["deploy", "configure", "test", "monitor"],
        "installed_models": ["orchestrator", "security", "ciec", "tcs", "knowledge", "installer"],
        "local_ki_present": true
    },
    "bridge": {
        "bridge_id": "bridge_a1b2c3d4",
        "master_url": "https://master-kiswarm.ngrok.io",
        "heartbeat_interval": 30,
        "status": "establishing"
    }
}
```

### 3. Heartbeat Protocol

Installer sends periodic heartbeats:

```json
{
    "protocol": "MasterKIInstaller/v6.3.0",
    "action": "heartbeat",
    "entity_id": "ki_installer_a1b2c3d4",
    "timestamp": "2025-01-01T00:10:00Z",
    "status": {
        "phase": "model_pull",
        "progress": 0.65,
        "models_installed": ["orchestrator", "security"],
        "models_pending": ["ciec", "tcs", "knowledge", "installer"],
        "errors": [],
        "warnings": []
    }
}
```

### 4. A2A Command Protocol

Master KISWARM can send commands to deployed installer:

```json
{
    "protocol": "MasterKIInstaller/v6.3.0",
    "action": "a2a_command",
    "message_id": "msg_xyz789",
    "timestamp": "2025-01-01T00:15:00Z",
    "from_entity": "master_kiswarm",
    "to_entity": "ki_installer_a1b2c3d4",
    "command": {
        "type": "status_report|model_pull|test_run|config_update|rollback",
        "params": {}
    }
}
```

### 5. Status Report Response

Installer responds with detailed status:

```json
{
    "protocol": "MasterKIInstaller/v6.3.0",
    "action": "status_report",
    "entity_id": "ki_installer_a1b2c3d4",
    "timestamp": "2025-01-01T00:20:00Z",
    "deployment": {
        "phase": "completed",
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-01T01:15:00Z",
        "duration_minutes": 75
    },
    "environment": {
        "type": "colab",
        "gpu_available": true,
        "gpu_type": "T4",
        "ram_gb": 16,
        "disk_free_gb": 100
    },
    "components": {
        "ollama": "running",
        "models": {
            "total": 6,
            "installed": ["orchestrator", "security", "ciec", "tcs", "knowledge", "installer"],
            "status": "all_operational"
        },
        "scada_layers": {
            "layer1_control": "active",
            "layer2_a2a_chat": "active",
            "layer3_shadow": "active",
            "layer4_tunnel": "active"
        }
    },
    "bridge": {
        "status": "connected",
        "uptime_minutes": 75,
        "messages_sent": 150,
        "messages_received": 5
    }
}
```

## Local KI Integration

When local KI (Gemini CLI, Qwen CLI, etc.) is available in target environment:

### Integration Protocol

```python
# KISWARM Installer discovers local KI
local_ki_discovery = {
    "action": "discover_local_ki",
    "types": ["gemini_cli", "qwen_cli", "ollama_local"],
    "bridge_path": "/tmp/kiswarm_bridge"
}

# Local KI registers as helper
local_ki_registration = {
    "entity_id": "local_gemini_cli",
    "entity_type": "local_ki",
    "capabilities": ["code_generation", "analysis", "debugging"],
    "bridge_socket": "/tmp/kiswarm_bridge/gemini.sock"
}

# Installer delegates tasks to local KI
delegation = {
    "action": "delegate",
    "task": "diagnose_error",
    "error_context": {...},
    "target_entity": "local_gemini_cli"
}
```

## Error Recovery

### Automatic Rollback Triggers

```json
{
    "rollback_triggers": [
        {"condition": "model_pull_timeout", "action": "partial_deployment"},
        {"condition": "master_connection_failed", "action": "standalone_mode"},
        {"condition": "disk_full", "action": "cleanup_and_retry"},
        {"condition": "critical_error", "action": "full_rollback"}
    ]
}
```

### Recovery Actions

```json
{
    "recovery_sequence": [
        {"step": 1, "action": "stop_all_services"},
        {"step": 2, "action": "cleanup_partial_downloads"},
        {"step": 3, "action": "restore_previous_config"},
        {"step": 4, "action": "report_failure_to_master"},
        {"step": 5, "action": "await_instructions"}
    ]
}
```

## Security

### Authorization Levels

| Level | Authorization | Capabilities |
|-------|---------------|--------------|
| Maquister_Equitum | Supreme | All operations, override all |
| HexStrike Agent | Deploy | Deploy installer, monitor |
| Master KISWARM | Control | Send commands, query status |
| Local KI | Assist | Help with local tasks only |

### Message Authentication

All messages are signed with entity private key:

```python
def sign_message(message: dict, private_key: str) -> str:
    """Sign message with entity private key."""
    message_str = json.dumps(message, sort_keys=True)
    signature = hashlib.sha256(f"{message_str}:{private_key}".encode()).hexdigest()
    return signature
```

## Implementation

### MasterKIInstaller Class

```python
class MasterKIInstallerBridge:
    """Bridge between deployed KISWARM Installer and Master KISWARM."""
    
    def __init__(self, master_url: str, entity_id: str):
        self.master_url = master_url
        self.entity_id = entity_id
        self.bridge_id = f"bridge_{entity_id}"
        self.heartbeat_interval = 30  # seconds
        self.message_queue = []
        self.running = False
    
    def establish_bridge(self) -> bool:
        """Establish permanent bridge connection."""
        # Register with Master
        # Start heartbeat thread
        # Start message poller
        pass
    
    def send_heartbeat(self, status: dict) -> bool:
        """Send heartbeat to Master."""
        pass
    
    def poll_commands(self) -> list:
        """Poll for A2A commands from Master."""
        pass
    
    def execute_command(self, command: dict) -> dict:
        """Execute command from Master."""
        pass
    
    def delegate_to_local_ki(self, task: dict) -> dict:
        """Delegate task to local KI if available."""
        pass
    
    def report_status(self) -> dict:
        """Report full status to Master."""
        pass
```

## Usage

### Deploy from HexStrike Agent

```python
from kiinstaller import AutonomousKISWARMInstaller, MasterKIInstallerBridge

# Create installer
installer = AutonomousKISWARMInstaller(
    master_url="https://master-kiswarm.ngrok.io",
    entity_id="ki_installer_colab_001"
)

# Deploy with bridge
result = installer.deploy()

# Bridge is automatically established
# Installer maintains permanent connection to Master
```

### Monitor from Master KISWARM

```bash
# List all deployed installers
curl https://master-kiswarm.ngrok.io/api/mesh/status | jq '.registered_nodes[] | select(.entity_type=="autonomous_installer")'

# Send command to specific installer
curl -X POST https://master-kiswarm.ngrok.io/api/mesh/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "from_entity": "master_kiswarm",
    "to_entity": "ki_installer_colab_001",
    "message_type": "command",
    "content": {"type": "status_report"}
  }'
```

---

*Protocol Version: 6.3.0*
*Last Updated: 2025-01-01*
*Author: Z.ai (GLM5) + Master KISWARM Collaboration*
