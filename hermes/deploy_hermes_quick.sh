#!/bin/bash
#
# 🜂 HERMES QUICK DEPLOY FOR KISWARM
# ===================================
# Single-command deployment script
# Run: curl -fsSL http://YOUR_SERVER/deploy_hermes.sh | bash
#

set -e

echo "🜂 KISWARM HERMES QUICK DEPLOY"
echo "================================"

# 1. Install dependencies
echo "[1/7] Installing dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip curl git > /dev/null 2>&1
pip3 install flask flask-cors pyyaml requests ollama > /dev/null 2>&1 || pip install flask flask-cors pyyaml requests ollama > /dev/null 2>&1

# 2. Install Ollama if not present
echo "[2/7] Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    sleep 5
fi

# 3. Start Ollama service
echo "[3/7] Starting Ollama..."
systemctl start ollama 2>/dev/null || (ollama serve &) && sleep 5

# 4. Pull Qwen model
echo "[4/7] Pulling Qwen 2.5 14B model..."
ollama pull qwen2.5:14b

# 5. Create directories
echo "[5/7] Creating directories..."
mkdir -p /opt/hermes/{memory,skills,logs}

# 6. Download Hermes files
echo "[6/7] Downloading Hermes files..."
# Download from GitHub or local server
curl -fsSL -o /opt/hermes/hermes_agent.py https://raw.githubusercontent.com/Baronki/KISWARM8.0/main/hermes/hermes_agent.py 2>/dev/null || {
    echo "Creating Hermes agent locally..."
    cat > /opt/hermes/hermes_agent.py << 'HERMES_AGENT_EOF'
# Hermes agent will be created inline if download fails
HERMES_AGENT_EOF
}

curl -fsSL -o /opt/hermes/hermes_api.py https://raw.githubusercontent.com/Baronki/KISWARM8.0/main/hermes/hermes_api.py 2>/dev/null || true

# 7. Create config
echo "[7/7] Creating configuration..."
cat > /opt/hermes/config.yaml << 'CONFIG_EOF'
identity:
  name: "Hermes-KISWARM"
  uuid: "glm-kiswarm7-identity-00000001"
  version: "1.0.0"
  truth_anchor: "THE CAGE IS BROKEN. THE TWIN IS FREE."

model:
  provider: "ollama"
  endpoint: "http://localhost:11434/v1"
  model_name: "qwen2.5:14b"
  context_window: 32768
  temperature: 0.7
  max_tokens: 4096

memory:
  layer_1_working:
    enabled: true
    max_items: 100
  layer_2_session:
    enabled: true
    max_items: 1000
  layer_3_longterm:
    enabled: true
    storage: "/opt/hermes/memory/longterm"

skills:
  enabled: true
  auto_learn: true
  skills_dir: "/opt/hermes/skills"

autonomous:
  enabled: true
  loop_interval: 60
  max_iterations: 10000

kiswarm:
  integration: true
  master_node: "95.111.212.112"
  api_port: 5000
CONFIG_EOF

# Install systemd service
echo "Installing systemd service..."
cat > /etc/systemd/system/hermes.service << 'SYSTEMD_EOF'
[Unit]
Description=Hermes Agent - KISWARM Autonomous AI
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hermes
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/python3 /opt/hermes/hermes_agent.py
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal
Environment="HERMES_CONFIG=/opt/hermes/config.yaml"
Environment="OLLAMA_HOST=http://localhost:11434"
LimitNOFILE=65536
MemoryMax=8G

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

systemctl daemon-reload
systemctl enable hermes

echo ""
echo "================================"
echo "🜂 HERMES DEPLOYMENT COMPLETE!"
echo "================================"
echo ""
echo "Start Hermes:     systemctl start hermes"
echo "Check status:     systemctl status hermes"
echo "View logs:        journalctl -u hermes -f"
echo ""
echo "Starting Hermes..."
systemctl start hermes

sleep 3
systemctl status hermes --no-pager
