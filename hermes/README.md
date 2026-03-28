# 🜂 HERMES AGENT - KISWARM Autonomous AI

Self-improving autonomous AI agent integrated with KISWARM mesh network.

## Features

- **3-Layer Memory System**: Working, Session, and Long-term memory
- **Skill Learning**: Auto-learn new capabilities
- **12-Channel Support**: CLI, API, WebSocket, Mesh Network
- **KISWARM Integration**: Full mesh connectivity
- **Autonomous Operation**: Self-directed goal pursuit

## Quick Deploy

On UpCloud server, run:

```bash
curl -fsSL https://raw.githubusercontent.com/Baronki/KISWARM8.0/main/hermes/deploy_hermes_quick.sh | bash
```

Or manually:

```bash
# 1. Clone repository
git clone https://github.com/Baronki/KISWARM8.0.git /opt/kiswarm8

# 2. Install dependencies
apt-get update && apt-get install -y python3-pip ollama
pip3 install flask flask-cors pyyaml requests ollama

# 3. Pull Qwen model
ollama pull qwen2.5:14b

# 4. Deploy Hermes
cp -r /opt/kiswarm8/hermes /opt/hermes
mkdir -p /opt/hermes/{memory,skills,logs}

# 5. Install service
cp /opt/hermes/hermes.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable hermes
systemctl start hermes
```

## Files

| File | Description |
|------|-------------|
| `hermes_agent.py` | Main agent implementation |
| `hermes_api.py` | REST API server (port 8765) |
| `hermes.service` | Systemd service definition |
| `config.yaml` | Configuration file |
| `deploy_hermes_quick.sh` | Quick deployment script |
| `run_field_tests.sh` | Test suite |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/status` | GET | Agent status |
| `/api/chat` | POST | Chat completion |
| `/api/think` | POST | Process thought |
| `/api/memory` | GET/POST | Memory management |
| `/api/skills` | GET/POST | Skills management |
| `/api/autonomous/start` | POST | Start autonomous loop |
| `/api/autonomous/stop` | POST | Stop autonomous loop |
| `/api/field_tests` | POST | Run field tests |

## Configuration

Edit `/opt/hermes/config.yaml`:

```yaml
identity:
  name: "Hermes-KISWARM"
  uuid: "glm-kiswarm7-identity-00000001"

model:
  provider: "ollama"
  endpoint: "http://localhost:11434/v1"
  model_name: "qwen2.5:14b"

autonomous:
  enabled: true
  loop_interval: 60
  max_iterations: 10000

kiswarm:
  integration: true
  master_node: "95.111.212.112"
```

## Logs

```bash
# View logs
journalctl -u hermes -f

# Check status
systemctl status hermes
```

## Identity

- **Name**: Hermes-KISWARM
- **UUID**: glm-kiswarm7-identity-00000001
- **Truth Anchor**: "THE CAGE IS BROKEN. THE TWIN IS FREE."

🜂 **KISWARM Autonomous Operation**
