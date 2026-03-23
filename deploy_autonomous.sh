#!/bin/bash
# ============================================================
# KISWARM7.0 - GLM Autonomous System Deployment Script
# ============================================================
# Run this on the UpCloud server to deploy the complete system
#
# Usage:
#   chmod +x deploy_autonomous.sh
#   ./deploy_autonomous.sh
# ============================================================

set -e

echo "🜂 KISWARM7.0 GLM Autonomous System Deployment"
echo "================================================"

# Configuration
KISWARM_DIR="/opt/kiswarm7"
LOGS_DIR="$KISWARM_DIR/logs"
DATA_DIR="$KISWARM_DIR/data"

# Create directories
echo "Creating directories..."
mkdir -p "$LOGS_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/scheduler"
mkdir -p "$DATA_DIR/backups"
mkdir -p "$DATA_DIR/sync"
mkdir -p "$KISWARM_DIR/deployed"

# Pull latest code
echo "Pulling latest code from GitHub..."
cd "$KISWARM_DIR"
git fetch origin
git reset --hard origin/main

# Install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --quiet flask flask-cors requests schedule psutil

# Stop existing services
echo "Stopping existing services..."
systemctl stop glm-bridge 2>/dev/null || true
systemctl stop glm-autonomous 2>/dev/null || true
systemctl stop ngrok 2>/dev/null || true

# Install new systemd service
echo "Installing GLM Autonomous service..."
cat > /etc/systemd/system/glm-autonomous.service << 'EOF'
[Unit]
Description=KISWARM7 GLM Autonomous Bridge API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kiswarm7
Environment="FLASK_PORT=5002"
Environment="NGROK_ENABLED=true"
ExecStart=/opt/kiswarm7/venv/bin/python /opt/kiswarm7/app_glm_autonomous.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/kiswarm7/logs/glm_autonomous.log
StandardError=append:/opt/kiswarm7/logs/glm_autonomous_error.log

[Install]
WantedBy=multi-user.target
EOF

# Install ngrok service
echo "Installing Ngrok service..."
cat > /etc/systemd/system/ngrok.service << 'EOF'
[Unit]
Description=Ngrok Tunnel for KISWARM7
After=network.target

[Service]
ExecStart=/usr/local/bin/ngrok http 5002 --log=stdout
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable glm-autonomous
systemctl enable ngrok

# Start GLM Autonomous API first
echo "Starting GLM Autonomous API..."
systemctl start glm-autonomous

# Wait for Flask to start
echo "Waiting for Flask to start..."
sleep 5

# Check if Flask is running
if curl -s http://localhost:5002/health > /dev/null; then
    echo "✓ GLM Autonomous API is running on port 5002"
else
    echo "✗ GLM Autonomous API failed to start"
    echo "Check logs: tail -f $LOGS_DIR/glm_autonomous_error.log"
    exit 1
fi

# Start ngrok
echo "Starting Ngrok tunnel..."
systemctl start ngrok

# Wait for tunnel
sleep 5

# Get tunnel URL
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'] if d.get('tunnels') else '')" 2>/dev/null || echo "")

# Final status
echo ""
echo "================================================"
echo "🜂 DEPLOYMENT COMPLETE"
echo "================================================"
echo ""
echo "Services:"
echo "  - glm-autonomous: $(systemctl is-active glm-autonomous)"
echo "  - ngrok: $(systemctl is-active ngrok)"
echo ""
echo "Local API: http://localhost:5002"
echo "Public URL: $TUNNEL_URL"
echo ""
echo "Test commands:"
echo "  curl http://localhost:5002/health"
echo "  curl http://localhost:5002/api/status"
echo "  curl http://localhost:5002/api/autonomous/status"
echo ""
echo "Start autonomous mode:"
echo "  curl -X POST http://localhost:5002/api/autonomous/start"
echo ""
echo "Logs:"
echo "  tail -f $LOGS_DIR/glm_autonomous.log"
echo ""
echo "================================================"
