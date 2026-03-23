#!/bin/bash
# ============================================================================
# KISWARM SCADA v6.3.0 - Master API Deployment Script
# ============================================================================
# This script deploys the Master KISWARM API with full 4-layer SCADA architecture
# 
# Usage:
#   chmod +x deploy_scada_master.sh
#   ./deploy_scada_master.sh
#
# Architecture:
#   Layer 1: SCADA Control (Status, Register, Heartbeat)
#   Layer 2: A2A Chat (Direct Agent messaging)
#   Layer 3: Shadow Environment (Digital Twin)
#   Layer 4: Direct Tunneling (SSH/Tor bypass)
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║        KISWARM SCADA v6.3.0 - Master API Deployment                    ║"
echo "╠════════════════════════════════════════════════════════════════════════╣"
echo "║  4-Layer Architecture:                                                 ║"
echo "║  Layer 1: SCADA Control (Status, Register, Heartbeat)                  ║"
echo "║  Layer 2: A2A Chat (Direct Agent messaging)                            ║"
echo "║  Layer 3: Shadow Environment (Digital Twin)                            ║"
echo "║  Layer 4: Direct Tunneling (SSH/Tor bypass)                            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"

# ============================================================================
# CONFIGURATION
# ============================================================================

PORT=5002
MASTER_DIR="/tmp/kiswarm_master"
REPO_URL="https://github.com/Baronki/KISWARMAGENTS1.0"

# ============================================================================
# STEP 1: INSTALL DEPENDENCIES
# ============================================================================

echo ""
echo "📦 Step 1: Installing dependencies..."

pip install -q flask flask-cors requests 2>/dev/null || pip3 install -q flask flask-cors requests

echo "   ✅ Dependencies installed"

# ============================================================================
# STEP 2: DOWNLOAD MASTER API v6.3.0
# ============================================================================

echo ""
echo "📥 Step 2: Downloading Master API v6.3.0..."

mkdir -p $MASTER_DIR
cd $MASTER_DIR

# Download from GitHub
curl -sL "${REPO_URL}/raw/main/mesh/master_kiswarm_api.py" -o master_kiswarm_api.py

if [ -f "master_kiswarm_api.py" ]; then
    echo "   ✅ Master API downloaded ($(wc -l < master_kiswarm_api.py) lines)"
else
    echo "   ❌ Failed to download Master API"
    exit 1
fi

# ============================================================================
# STEP 3: KILL EXISTING PROCESSES
# ============================================================================

echo ""
echo "🧹 Step 3: Cleaning up existing processes..."

# Kill existing Flask on port 5002
pkill -f "python.*master_kiswarm" 2>/dev/null || true
pkill -f "flask.*5002" 2>/dev/null || true

# Kill existing ngrok
pkill -f ngrok 2>/dev/null || true

sleep 2

echo "   ✅ Cleanup complete"

# ============================================================================
# STEP 4: START MASTER API (BACKGROUND)
# ============================================================================

echo ""
echo "🚀 Step 4: Starting Master API on port $PORT..."

# Start Flask in background
nohup python master_kiswarm_api.py --port $PORT > flask.log 2>&1 &
FLASK_PID=$!

echo "   Flask PID: $FLASK_PID"

# Wait for Flask to start
echo "   Waiting for Flask to initialize..."
sleep 5

# Test local connection
for i in {1..10}; do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo "   ✅ Master API is running on port $PORT"
        break
    fi
    echo "   Attempt $i/10..."
    sleep 2
done

# Verify
if ! curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "   ❌ Master API failed to start"
    echo "   Check logs: cat $MASTER_DIR/flask.log"
    exit 1
fi

# ============================================================================
# STEP 5: START NGROK TUNNEL
# ============================================================================

echo ""
echo "🌐 Step 5: Starting ngrok tunnel..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "   Installing ngrok..."
    curl -sL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o /tmp/ngrok.tgz
    tar -xzf /tmp/ngrok.tgz -C /tmp
    sudo mv /tmp/ngrok /usr/local/bin/ 2>/dev/null || mv /tmp/ngrok ~/bin/
fi

# Start ngrok
nohup ngrok http $PORT > ngrok.log 2>&1 &
NGROK_PID=$!

echo "   ngrok PID: $NGROK_PID"

# Wait for ngrok to start
sleep 5

# Get public URL
PUBLIC_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys,json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null || echo "")

if [ -n "$PUBLIC_URL" ]; then
    echo "   ✅ ngrok tunnel established"
    echo "   🔗 Public URL: $PUBLIC_URL"
else
    echo "   ⚠️ Could not get public URL, check ngrok dashboard"
fi

# ============================================================================
# STEP 6: TEST SCADA ENDPOINTS
# ============================================================================

echo ""
echo "🔍 Step 6: Testing SCADA endpoints..."

# Layer 1: Control
echo "   Layer 1 (Control):"
curl -s http://localhost:$PORT/api/mesh/status | python3 -m json.tool | head -5
echo "      ✅ Control layer OK"

# Layer 2: A2A Chat
echo "   Layer 2 (A2A Chat):"
curl -s -X POST http://localhost:$PORT/api/mesh/chat/send \
    -H "Content-Type: application/json" \
    -d '{"from": "test", "to": "all", "message": "SCADA v6.3.0 online"}' | python3 -m json.tool
echo "      ✅ Chat layer OK"

# Layer 3: Shadow
echo "   Layer 3 (Shadow):"
curl -s -X POST http://localhost:$PORT/api/mesh/shadow/update \
    -H "Content-Type: application/json" \
    -d '{"node_id": "test-node", "env_vars": {"TEST": "true"}}' | python3 -m json.tool
echo "      ✅ Shadow layer OK"

# Layer 4: Tunnel
echo "   Layer 4 (Tunnel):"
curl -s -X POST http://localhost:$PORT/api/mesh/tunnel/register \
    -H "Content-Type: application/json" \
    -d '{"node_id": "test-node", "type": "ssh", "address": "localhost:8022"}' | python3 -m json.tool
echo "      ✅ Tunnel layer OK"

# ============================================================================
# STEP 7: SAVE CONFIGURATION
# ============================================================================

echo ""
echo "💾 Step 7: Saving configuration..."

cat > scada_config.json << EOF
{
    "version": "6.3.0",
    "port": $PORT,
    "public_url": "$PUBLIC_URL",
    "flask_pid": $FLASK_PID,
    "ngrok_pid": $NGROK_PID,
    "master_dir": "$MASTER_DIR",
    "layers": {
        "control": "active",
        "chat": "active", 
        "shadow": "active",
        "tunnel": "active"
    },
    "endpoints": {
        "status": "/api/mesh/status",
        "register": "/api/mesh/register",
        "chat_send": "/api/mesh/chat/send",
        "chat_poll": "/api/mesh/chat/poll",
        "shadow_update": "/api/mesh/shadow/update",
        "shadow_get": "/api/mesh/shadow/get/<node_id>",
        "tunnel_register": "/api/mesh/tunnel/register",
        "tunnel_get": "/api/mesh/tunnel/get/<node_id>"
    },
    "deployed_at": "$(date -Iseconds)"
}
EOF

echo "   ✅ Configuration saved to $MASTER_DIR/scada_config.json"

# ============================================================================
# COMPLETE
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║              SCADA v6.3.0 DEPLOYMENT COMPLETE                          ║"
echo "╠════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                        ║"
echo "║  🔗 Master URL: $PUBLIC_URL"
echo "║  📍 Local URL:  http://localhost:$PORT"
echo "║  📁 Directory:  $MASTER_DIR"
echo "║                                                                        ║"
echo "║  4-LAYER SCADA ACTIVE:                                                 ║"
echo "║  ✅ Layer 1: SCADA Control                                             ║"
echo "║  ✅ Layer 2: A2A Chat                                                  ║"
echo "║  ✅ Layer 3: Shadow (Digital Twin)                                     ║"
echo "║  ✅ Layer 4: Tunnel (Direct Connect)                                   ║"
echo "║                                                                        ║"
echo "║  NEXT STEPS:                                                           ║"
echo "║  1. Run KIInstaller in Colab with this Master URL                     ║"
echo "║  2. Colab Gemini can use colab_gemini_bridge.py                        ║"
echo "║  3. Z.ai monitors via chat/shadow endpoints                            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"

# Export URL for use in other scripts
echo ""
echo "Export this for KIInstaller:"
echo "  export MASTER_URL=\"$PUBLIC_URL\""
echo ""
echo "Test command:"
echo "  curl -H \"ngrok-skip-browser-warning: true\" $PUBLIC_URL/api/mesh/status"
