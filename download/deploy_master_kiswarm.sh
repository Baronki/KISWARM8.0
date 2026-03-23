#!/bin/bash
#
# KISWARM6.0 - Master KISWARM ngrok Deployment Script
# ====================================================
# Save this file as: deploy_master_kiswarm.sh
# Run: bash deploy_master_kiswarm.sh
#
# This script runs on YOUR local machine (where you logged into ngrok)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration - UPDATE THIS WITH YOUR ACTUAL AUTHTOKEN
NGROK_AUTH_TOKEN="3Ac51HC51vmerRvn9CodFhxgnYN_771JYNNWUuwi4uQyucxHx"
API_PORT=5001

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   ${BOLD}KISWARM6.0 - MASTER KISWARM DEPLOYMENT${NC}${CYAN}                    ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# STEP 1: Check Python
echo -e "${BLUE}[STEP 1] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python3 found: $(python3 --version)${NC}"
else
    echo -e "${RED}✗ Python3 not found. Please install Python 3 first.${NC}"
    exit 1
fi

# STEP 2: Install Python dependencies
echo -e "${BLUE}[STEP 2] Installing Python dependencies...${NC}"
pip3 install flask flask-cors requests websockets 2>/dev/null || pip install flask flask-cors requests websockets 2>/dev/null
echo -e "${GREEN}✓ Dependencies installed${NC}"

# STEP 3: Check ngrok
echo -e "${BLUE}[STEP 3] Checking ngrok...${NC}"
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}ngrok not found. You mentioned you already have ngrok dashboard open.${NC}"
    echo -e "${YELLOW}Please install ngrok first from your dashboard or run:${NC}"
    echo ""
    echo "  curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null"
    echo "  echo 'deb https://ngrok-agent.s3.amazonaws.com bookworm main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
    echo "  sudo apt update && sudo apt install ngrok"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ ngrok found: $(ngrok version)${NC}"
fi

# STEP 4: Configure ngrok authtoken
echo -e "${BLUE}[STEP 4] Configuring ngrok authtoken...${NC}"
ngrok config add-authtoken $NGROK_AUTH_TOKEN 2>/dev/null || echo "Already configured"
echo -e "${GREEN}✓ ngrok configured${NC}"

# STEP 5: Clean up old processes
echo -e "${BLUE}[STEP 5] Cleaning up old processes...${NC}"
pkill -f "simple_master_api" 2>/dev/null || true
pkill -f ngrok 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Cleanup complete${NC}"

# STEP 6: Create simple Master API server
echo -e "${BLUE}[STEP 6] Creating Master API server...${NC}"

cat > /tmp/simple_master_api.py << 'PYEOF'
#!/usr/bin/env python3
"""
KISWARM6.0 - Simple Master API Server
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import time
import uuid
import os

app = Flask(__name__)
CORS(app)

# Storage
STATE_FILE = "/tmp/kiswarm_state.json"
MESSAGES_FILE = "/tmp/kiswarm_messages.json"

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except: pass
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize
if not os.path.exists(STATE_FILE):
    save_json(STATE_FILE, {"mesh_status": "online", "nodes": {}, "statistics": {}})
if not os.path.exists(MESSAGES_FILE):
    save_json(MESSAGES_FILE, {"pending": [], "processed": []})

@app.route('/api/mesh/status', methods=['GET'])
def get_status():
    state = load_json(STATE_FILE, {})
    return jsonify({"status": "online", "mesh_status": state.get("mesh_status", "unknown"), 
                    "nodes_count": len(state.get("nodes", {})), "timestamp": time.time()})

@app.route('/api/mesh/state', methods=['GET'])
def get_state():
    return jsonify(load_json(STATE_FILE, {}))

@app.route('/api/mesh/messages', methods=['GET'])
def get_messages():
    data = load_json(MESSAGES_FILE, {"pending": [], "processed": []})
    messages = data["pending"][:50]
    return jsonify({"count": len(messages), "messages": messages, "timestamp": time.time()})

@app.route('/api/mesh/register', methods=['POST'])
def register():
    data = request.json or {}
    installer_id = str(uuid.uuid4())
    
    state = load_json(STATE_FILE, {"nodes": {}})
    state["nodes"][installer_id] = {
        "node_id": installer_id,
        "node_name": data.get("installer_name", "unknown"),
        "environment": data.get("environment", "unknown"),
        "capabilities": data.get("capabilities", []),
        "status": "online",
        "last_seen": time.time()
    }
    save_json(STATE_FILE, state)
    
    print(f"[REGISTER] {data.get('installer_name')} -> {installer_id}")
    return jsonify({"installer_id": installer_id, "status": "registered", 
                    "message": "Welcome to Master KISWARM!"})

@app.route('/api/mesh/status/<installer_id>', methods=['POST'])
def report_status(installer_id):
    data = request.json or {}
    
    # Add to messages
    msgs = load_json(MESSAGES_FILE, {"pending": []})
    msgs["pending"].append({
        "message_id": str(uuid.uuid4()),
        "message_type": "status_update",
        "sender_id": installer_id,
        "timestamp": time.time(),
        "payload": data
    })
    save_json(MESSAGES_FILE, msgs)
    
    # Update node
    state = load_json(STATE_FILE, {"nodes": {}})
    if installer_id in state.get("nodes", {}):
        state["nodes"][installer_id].update({
            "status": data.get("status"),
            "last_seen": time.time()
        })
        save_json(STATE_FILE, state)
    
    print(f"[STATUS] {installer_id[:8]}...: {data.get('status')} - {data.get('task', '')}")
    return jsonify({"status": "acknowledged"})

@app.route('/api/mesh/error/<installer_id>', methods=['POST'])
def report_error(installer_id):
    data = request.json or {}
    
    msgs = load_json(MESSAGES_FILE, {"pending": []})
    msgs["pending"].append({
        "message_id": str(uuid.uuid4()),
        "message_type": "error_report",
        "sender_id": installer_id,
        "priority": 0,
        "timestamp": time.time(),
        "payload": data
    })
    save_json(MESSAGES_FILE, msgs)
    
    print(f"[ERROR] {installer_id[:8]}...: {data.get('error_type')} - {data.get('error_message')}")
    return jsonify({"status": "acknowledged", "message": "Error logged, awaiting fix"})

@app.route('/api/mesh/fix', methods=['POST'])
def send_fix():
    data = request.json or {}
    installer_id = data.get("installer_id")
    
    msgs = load_json(MESSAGES_FILE, {"pending": []})
    msgs["pending"].append({
        "message_id": str(uuid.uuid4()),
        "message_type": "fix_suggestion",
        "sender_id": "z_ai",
        "receiver_id": installer_id,
        "timestamp": time.time(),
        "payload": data
    })
    save_json(MESSAGES_FILE, msgs)
    
    print(f"[FIX] Sent to {installer_id[:8] if installer_id else 'unknown'}...: {data.get('title', '')}")
    return jsonify({"status": "queued", "fix": data, "timestamp": time.time()})

@app.route('/api/mesh/abort', methods=['POST'])
def abort():
    data = request.json or {}
    installer_id = data.get("installer_id")
    
    msgs = load_json(MESSAGES_FILE, {"pending": []})
    msgs["pending"].append({
        "message_id": str(uuid.uuid4()),
        "message_type": "abort",
        "sender_id": "z_ai",
        "receiver_id": installer_id,
        "timestamp": time.time(),
        "payload": {"reason": data.get("reason", "Aborted by Z.ai")}
    })
    save_json(MESSAGES_FILE, msgs)
    
    print(f"[ABORT] Sent to {installer_id[:8] if installer_id else 'unknown'}...")
    return jsonify({"status": "queued", "reason": data.get("reason")})

@app.route('/api/mesh/heartbeat/<installer_id>', methods=['POST'])
def heartbeat(installer_id):
    state = load_json(STATE_FILE, {"nodes": {}})
    if installer_id in state.get("nodes", {}):
        state["nodes"][installer_id]["last_seen"] = time.time()
        save_json(STATE_FILE, state)
    return jsonify({"status": "acknowledged"})

if __name__ == '__main__':
    print("Starting Master KISWARM API on port 5001...")
    app.run(host='0.0.0.0', port=5001, threaded=True)
PYEOF

echo -e "${GREEN}✓ API server created at /tmp/simple_master_api.py${NC}"

# STEP 7: Start API server
echo -e "${BLUE}[STEP 7] Starting API server...${NC}"
python3 /tmp/simple_master_api.py > /tmp/kiswarm_api.log 2>&1 &
API_PID=$!
sleep 2

if kill -0 $API_PID 2>/dev/null; then
    echo -e "${GREEN}✓ API server started (PID: $API_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start API server${NC}"
    cat /tmp/kiswarm_api.log
    exit 1
fi

# STEP 8: Start ngrok
echo -e "${BLUE}[STEP 8] Starting ngrok tunnel...${NC}"
ngrok http $API_PORT --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
sleep 4

# Get public URL
PUBLIC_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'] if d.get('tunnels') else '')" 2>/dev/null)

if [ -z "$PUBLIC_URL" ]; then
    echo -e "${YELLOW}⚠ Could not auto-detect URL. Check ngrok dashboard at http://127.0.0.1:4040${NC}"
    PUBLIC_URL="https://YOUR-URL.ngrok-free.app"
fi

# Save URL
echo "$PUBLIC_URL" > /tmp/kiswarm_master_url.txt

# SUCCESS
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ${BOLD}✓ MASTER KISWARM IS ONLINE!${NC}${GREEN}                                ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}📡 YOUR PUBLIC URL:${NC}"
echo -e "    ${CYAN}${PUBLIC_URL}${NC}"
echo ""
echo -e "${BOLD}📋 COPY THIS FOR COLAB:${NC}"
echo ""
echo -e "    MASTER_KISWARM_URL = \"${PUBLIC_URL}\""
echo ""
echo -e "${BOLD}📊 MONITORING:${NC}"
echo -e "    ngrok Dashboard: http://127.0.0.1:4040"
echo -e "    API Status:      curl ${PUBLIC_URL}/api/mesh/status"
echo ""
echo -e "${BOLD}🛑 TO STOP:${NC}"
echo -e "    pkill -f simple_master_api; pkill -f ngrok"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Test
echo -e "${BLUE}Testing connection...${NC}"
sleep 1
curl -s "${PUBLIC_URL}/api/mesh/status" | python3 -m json.tool || echo "Test may fail if ngrok not fully ready"
echo ""
