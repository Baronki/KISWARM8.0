#!/bin/bash
# KISWARM7.0 - Complete Deployment Fix
# Run this on UpCloud server

echo "🜂 KISWARM7.0 Complete Deployment"

# 1. Fix git and pull latest
cd /opt/kiswarm7
git fetch origin
git reset --hard origin/main
git clean -fd

# 2. Install dependencies
source venv/bin/activate
pip install --quiet flask flask-cors requests schedule psutil

# 3. Create directories
mkdir -p /opt/kiswarm7/logs
mkdir -p /opt/kiswarm7/data/scheduler
mkdir -p /opt/kiswarm7/data/backups
mkdir -p /opt/kiswarm7/data/sync
mkdir -p /opt/kiswarm7/deployed

# 4. Stop old services
systemctl stop glm-bridge 2>/dev/null || true
systemctl stop glm-autonomous 2>/dev/null || true
systemctl stop ngrok 2>/dev/null || true

# 5. Install new GLM Autonomous service
cat > /etc/systemd/system/glm-autonomous.service << 'SERVICE'
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
SERVICE

# 6. Install ngrok service
cat > /etc/systemd/system/ngrok.service << 'SERVICE'
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
SERVICE

# 7. Reload and enable
systemctl daemon-reload
systemctl enable glm-autonomous
systemctl enable ngrok

# 8. Start GLM Autonomous API
echo "Starting GLM Autonomous API..."
systemctl start glm-autonomous
sleep 5

# 9. Check if running
if curl -s http://localhost:5002/health > /dev/null 2>&1; then
    echo "✓ GLM Autonomous API running on port 5002"
else
    echo "✗ GLM Autonomous API failed - checking logs..."
    tail -20 /opt/kiswarm7/logs/glm_autonomous_error.log
fi

# 10. Start ngrok
echo "Starting Ngrok tunnel..."
systemctl start ngrok
sleep 5

# 11. Get public URL
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'] if d.get('tunnels') else '')" 2>/dev/null || echo "waiting...")

# 12. Final status
echo ""
echo "=========================================="
echo "🜂 DEPLOYMENT STATUS"
echo "=========================================="
echo ""
echo "Services:"
systemctl is-active glm-autonomous ngrok
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
echo "=========================================="
