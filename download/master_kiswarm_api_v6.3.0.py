#!/usr/bin/env python3
"""
KISWARM6.0 - Master KISWARM API Server
======================================
Flask-based REST API for KI-to-KI Mesh Communication
SCADA-Grade 4-Layer Architecture v6.3.0

This server provides:
LAYER 1 - SCADA Control: Registration, Status, Heartbeat
LAYER 2 - A2A Chat: Direct Agent-to-Agent messaging
LAYER 3 - Shadow Environment: Digital Twin telemetry
LAYER 4 - Direct Tunneling: SSH/Tor bypass registration

Architecture:
    ┌───────────────────┬────────────────────┬──────────────────────────┐
    │ Layer             │ Component          │ Function                 │
    ├───────────────────┼────────────────────┼──────────────────────────┤
    │ Field Layer       │ KIInstaller        │ Local execution & bridge │
    │ Edge Layer        │ Colab Gemini       │ Fast local reasoning     │
    │ Control Layer     │ Master API         │ Message Broker (PLC)     │
    │ Supervisory Layer │ Z.ai (GLM5)        │ Global Strategy          │
    └───────────────────┴────────────────────┴──────────────────────────┘

Setup:
    pip install flask flask-cors
    python master_kiswarm_api.py --port 5002

Author: KISWARM Development Team (Z.ai + Gemini CLI Collaboration)
Version: 6.3.0 SCADA Architecture
License: See LICENSE file
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import time
import uuid
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MasterKISWARM')

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_PORT = 5002
DEFAULT_HOST = '0.0.0.0'

# Storage files
STATE_FILE = "/tmp/kiswarm_state.json"
MESSAGES_FILE = "/tmp/kiswarm_messages.json"
CHAT_FILE = "/tmp/kiswarm_chat.json"           # Layer 2: A2A Chat
SHADOW_FILE = "/tmp/kiswarm_shadow.json"       # Layer 3: Digital Twin
TUNNEL_FILE = "/tmp/kiswarm_tunnels.json"      # Layer 4: Direct Tunneling

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_json(path: str, default: Any = None) -> Any:
    """Load JSON file safely"""
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading {path}: {e}")
    return default if default is not None else {}

def save_json(path: str, data: Any) -> bool:
    """Save JSON file safely"""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving {path}: {e}")
        return False

def initialize_storage():
    """Initialize all storage files"""
    # Layer 1: State
    if not os.path.exists(STATE_FILE):
        initial_state = {
            "mesh_status": "online",
            "nodes": {},
            "statistics": {
                "messages_total": 0,
                "errors_total": 0,
                "fixes_sent": 0,
                "last_update": time.time()
            },
            "created_at": time.time()
        }
        save_json(STATE_FILE, initial_state)
        logger.info("Initialized state file")
    
    # Layer 1: Messages
    if not os.path.exists(MESSAGES_FILE):
        initial_messages = {
            "pending": [],
            "processed": [],
            "created_at": time.time()
        }
        save_json(MESSAGES_FILE, initial_messages)
        logger.info("Initialized messages file")
    
    # Layer 2: Chat
    if not os.path.exists(CHAT_FILE):
        save_json(CHAT_FILE, {"messages": []})
        logger.info("Initialized chat file")
    
    # Layer 3: Shadow (Digital Twin)
    if not os.path.exists(SHADOW_FILE):
        save_json(SHADOW_FILE, {"nodes": {}})
        logger.info("Initialized shadow file")
    
    # Layer 4: Tunnels
    if not os.path.exists(TUNNEL_FILE):
        save_json(TUNNEL_FILE, {"tunnels": {}})
        logger.info("Initialized tunnels file")

# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ============================================================================
# LAYER 1: SCADA CONTROL (Status & Register)
# ============================================================================

@app.route('/api/mesh/status', methods=['GET'])
def get_status():
    """
    Get overall mesh status.
    
    Returns:
        {
            "status": "online",
            "mesh_status": "online",
            "nodes_count": 1,
            "timestamp": 1234567890.123
        }
    """
    state = load_json(STATE_FILE, {})
    return jsonify({
        "status": "online",
        "mesh_status": state.get("mesh_status", "unknown"),
        "nodes_count": len(state.get("nodes", {})),
        "timestamp": time.time()
    })

@app.route('/api/mesh/state', methods=['GET'])
def get_state():
    """Get full mesh state including all registered nodes."""
    return jsonify(load_json(STATE_FILE, {}))

@app.route('/api/mesh/nodes', methods=['GET'])
def get_nodes():
    """Get list of all registered nodes"""
    state = load_json(STATE_FILE, {})
    nodes = state.get("nodes", {})
    return jsonify(list(nodes.values()))

@app.route('/api/mesh/nodes/<node_id>', methods=['GET'])
def get_node(node_id: str):
    """Get specific node details"""
    state = load_json(STATE_FILE, {})
    node = state.get("nodes", {}).get(node_id)
    if not node:
        return jsonify({"error": "Node not found"}), 404
    return jsonify(node)

# ============================================================================
# LAYER 1: MESSAGE ENDPOINTS
# ============================================================================

@app.route('/api/mesh/messages', methods=['GET'])
def get_messages():
    """
    Get pending messages from KIInstallers.
    
    This is what Z.ai polls to see what's happening.
    """
    limit = request.args.get('limit', 50, type=int)
    data = load_json(MESSAGES_FILE, {"pending": []})
    messages = data.get("pending", [])[:limit]
    
    return jsonify({
        "count": len(messages),
        "messages": messages,
        "timestamp": time.time()
    })

@app.route('/api/mesh/messages/latest', methods=['GET'])
def get_latest_message():
    """Get the most recent message"""
    data = load_json(MESSAGES_FILE, {"pending": []})
    messages = data.get("pending", [])
    if messages:
        return jsonify(messages[-1])
    return jsonify({"message": None})

# ============================================================================
# LAYER 1: REGISTRATION ENDPOINTS
# ============================================================================

@app.route('/api/mesh/register', methods=['POST'])
def register():
    """
    Register a new KIInstaller instance.
    
    Request Body:
        {
            "installer_name": "colab-fieldtest-002",
            "environment": "colab",
            "capabilities": ["install", "deploy", "report", "bridge", "telemetry"]
        }
    
    Returns:
        {
            "installer_id": "uuid",
            "status": "registered",
            "message": "Welcome to Master KISWARM!"
        }
    """
    data = request.json or {}
    
    installer_id = str(uuid.uuid4())
    installer_name = data.get("installer_name", "unknown")
    environment = data.get("environment", "unknown")
    capabilities = data.get("capabilities", [])
    
    # Update state
    state = load_json(STATE_FILE, {"nodes": {}})
    state["nodes"][installer_id] = {
        "node_id": installer_id,
        "node_name": installer_name,
        "environment": environment,
        "capabilities": capabilities,
        "status": "online",
        "last_seen": time.time(),
        "registered_at": time.time()
    }
    state["statistics"]["last_update"] = time.time()
    save_json(STATE_FILE, state)
    
    logger.info(f"[REGISTER] {installer_name} -> {installer_id}")
    
    return jsonify({
        "installer_id": installer_id,
        "status": "registered",
        "message": "Welcome to Master KISWARM!",
        "config": {
            "heartbeat_interval": 30,
            "message_timeout": 60,
            "bridge_dir": "/tmp/kiswarm_bridge",
            "scada_layers": ["control", "chat", "shadow", "tunnel"]
        }
    })

@app.route('/api/mesh/heartbeat/<installer_id>', methods=['POST'])
def heartbeat(installer_id: str):
    """Process heartbeat from KIInstaller"""
    state = load_json(STATE_FILE, {"nodes": {}})
    
    if installer_id in state.get("nodes", {}):
        state["nodes"][installer_id]["last_seen"] = time.time()
        state["nodes"][installer_id]["status"] = "online"
        save_json(STATE_FILE, state)
        return jsonify({"status": "acknowledged"})
    
    return jsonify({"error": "Unknown installer"}), 404

# ============================================================================
# LAYER 1: STATUS REPORTING
# ============================================================================

@app.route('/api/mesh/status/<installer_id>', methods=['POST'])
def report_status(installer_id: str):
    """
    Report status from KIInstaller.
    
    Request Body:
        {
            "status": "installing",
            "task": "Deploying M60 module",
            "progress": 45,
            "details": {...}
        }
    """
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
    
    # Update node state
    state = load_json(STATE_FILE, {"nodes": {}})
    if installer_id in state.get("nodes", {}):
        state["nodes"][installer_id]["status"] = data.get("status", "unknown")
        state["nodes"][installer_id]["last_seen"] = time.time()
        state["nodes"][installer_id]["current_task"] = data.get("task")
        state["nodes"][installer_id]["progress"] = data.get("progress")
        state["statistics"]["messages_total"] = state["statistics"].get("messages_total", 0) + 1
        save_json(STATE_FILE, state)
    
    logger.info(f"[STATUS] {installer_id[:8]}...: {data.get('status')} - {data.get('task', '')} ({data.get('progress', 0)}%)")
    
    return jsonify({"status": "acknowledged"})

# ============================================================================
# LAYER 1: ERROR REPORTING
# ============================================================================

@app.route('/api/mesh/error/<installer_id>', methods=['POST'])
def report_error(installer_id: str):
    """
    Report error from KIInstaller.
    
    This triggers Z.ai notification for potential intervention.
    """
    data = request.json or {}
    
    # Add as high-priority message
    msgs = load_json(MESSAGES_FILE, {"pending": []})
    msgs["pending"].append({
        "message_id": str(uuid.uuid4()),
        "message_type": "error_report",
        "sender_id": installer_id,
        "priority": 0,  # Highest priority
        "timestamp": time.time(),
        "payload": data
    })
    save_json(MESSAGES_FILE, msgs)
    
    # Update statistics
    state = load_json(STATE_FILE, {})
    state["statistics"]["errors_total"] = state["statistics"].get("errors_total", 0) + 1
    save_json(STATE_FILE, state)
    
    logger.warning(f"[ERROR] {installer_id[:8]}...: {data.get('error_type')} - {data.get('error_message')}")
    
    return jsonify({
        "status": "acknowledged",
        "message": "Error logged, awaiting fix from Z.ai"
    })

# ============================================================================
# LAYER 1: FIX DELIVERY
# ============================================================================

@app.route('/api/mesh/fix', methods=['POST'])
def send_fix():
    """
    Send fix suggestion from Z.ai to KIInstaller.
    
    Request Body:
        {
            "installer_id": "target-installer-id",
            "fix_type": "pip_install",
            "title": "Install flask-cors",
            "description": "The flask_cors module is required",
            "solution": {
                "action": "pip install flask-cors",
                "commands": ["pip install flask-cors"]
            },
            "confidence": 0.98
        }
    """
    data = request.json or {}
    installer_id = data.get("installer_id")
    
    # Add as fix message
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
    
    # Update statistics
    state = load_json(STATE_FILE, {})
    state["statistics"]["fixes_sent"] = state["statistics"].get("fixes_sent", 0) + 1
    save_json(STATE_FILE, state)
    
    logger.info(f"[FIX] Sent to {installer_id[:8] if installer_id else 'unknown'}...: {data.get('title', '')}")
    
    return jsonify({
        "status": "queued",
        "fix": data,
        "timestamp": time.time()
    })

# ============================================================================
# LAYER 2: A2A CHAT (Direct Agent Communication)
# ============================================================================

@app.route('/api/mesh/chat/send', methods=['POST'])
def send_chat():
    """
    Send A2A chat message.
    
    Enables direct AI-to-AI dialogue:
    - Z.ai sends: {"from": "z_ai", "to": "colab_gemini", "message": "Analyze CUDA drivers"}
    - Colab Gemini receives via poll
    
    Request Body:
        {
            "from": "sender_id",
            "to": "receiver_id or 'all'",
            "message": "The message content"
        }
    """
    data = request.json or {}
    chat = load_json(CHAT_FILE, {"messages": []})
    
    message = {
        "id": str(uuid.uuid4()),
        "from": data.get("from", "unknown"),
        "to": data.get("to", "all"),
        "message": data.get("message", ""),
        "timestamp": time.time()
    }
    
    chat["messages"].append(message)
    # Keep last 100 messages
    chat["messages"] = chat["messages"][-100:]
    save_json(CHAT_FILE, chat)
    
    print(f"[CHAT] {message['from']} -> {message['to']}: {message['message'][:50]}...")
    
    return jsonify({"status": "sent", "id": message["id"]})

@app.route('/api/mesh/chat/poll', methods=['GET'])
def poll_chat():
    """
    Poll for chat messages.
    
    Query Parameters:
        target: Filter messages for this recipient (default: 'all')
    
    Returns messages addressed to 'target' or broadcast ('all')
    """
    target = request.args.get('target', 'all')
    chat = load_json(CHAT_FILE, {"messages": []})
    
    # Filter messages for me or broadcast
    messages = [m for m in chat["messages"] if m["to"] == target or m["to"] == "all"]
    
    return jsonify({"messages": messages})

# ============================================================================
# LAYER 3: SHADOW ENVIRONMENT (Digital Twin)
# ============================================================================

@app.route('/api/mesh/shadow/update', methods=['POST'])
def update_shadow():
    """
    Update Digital Twin shadow environment.
    
    The Colab environment is mirrored locally at the Master node.
    Telemetry includes: env_vars, file_tree, active_processes
    
    Request Body:
        {
            "node_id": "installer-uuid",
            "env_vars": {...},
            "file_tree": [...],
            "processes": [...]
        }
    """
    data = request.json or {}
    node_id = data.get("node_id")
    shadow = load_json(SHADOW_FILE, {"nodes": {}})
    
    if node_id:
        shadow["nodes"][node_id] = {
            "last_update": time.time(),
            "env_vars": data.get("env_vars", {}),
            "file_tree": data.get("file_tree", []),
            "active_processes": data.get("processes", [])
        }
        save_json(SHADOW_FILE, shadow)
        print(f"[SHADOW] Updated Digital Twin for {node_id}")
        return jsonify({"status": "updated"})
    
    return jsonify({"status": "error", "message": "Missing node_id"}), 400

@app.route('/api/mesh/shadow/get/<node_id>', methods=['GET'])
def get_shadow(node_id):
    """
    Get Digital Twin shadow for a specific node.
    
    Returns the mirrored environment state.
    """
    shadow = load_json(SHADOW_FILE, {"nodes": {}})
    return jsonify(shadow["nodes"].get(node_id, {}))

@app.route('/api/mesh/shadow/list', methods=['GET'])
def list_shadows():
    """List all nodes with shadow environments"""
    shadow = load_json(SHADOW_FILE, {"nodes": {}})
    return jsonify({
        "nodes": list(shadow["nodes"].keys()),
        "count": len(shadow["nodes"])
    })

# ============================================================================
# LAYER 4: DIRECT TUNNELING (Black Ops)
# ============================================================================

@app.route('/api/mesh/tunnel/register', methods=['POST'])
def register_tunnel():
    """
    Register a direct tunnel for bypassing the Master API.
    
    Types:
    - ssh: Reverse SSH tunnel
    - tor: Tor Hidden Service (.onion)
    - tcp: Raw TCP socket
    
    Request Body:
        {
            "node_id": "installer-uuid",
            "type": "ssh|tor|tcp",
            "address": "localhost:port or .onion address"
        }
    """
    data = request.json or {}
    node_id = data.get("node_id")
    tunnel_type = data.get("type", "unknown")
    address = data.get("address", "")
    
    tunnels = load_json(TUNNEL_FILE, {"tunnels": {}})
    tunnels["tunnels"][node_id] = {
        "type": tunnel_type,
        "address": address,
        "timestamp": time.time()
    }
    save_json(TUNNEL_FILE, tunnels)
    
    print(f"[TUNNEL] Direct Link Established: {node_id} via {tunnel_type} @ {address}")
    
    return jsonify({"status": "registered"})

@app.route('/api/mesh/tunnel/get/<node_id>', methods=['GET'])
def get_tunnel(node_id):
    """Get tunnel information for a specific node"""
    tunnels = load_json(TUNNEL_FILE, {"tunnels": {}})
    return jsonify(tunnels["tunnels"].get(node_id, {}))

@app.route('/api/mesh/tunnel/list', methods=['GET'])
def list_tunnels():
    """List all registered tunnels"""
    tunnels = load_json(TUNNEL_FILE, {"tunnels": {}})
    return jsonify({
        "tunnels": tunnels["tunnels"],
        "count": len(tunnels["tunnels"])
    })

# ============================================================================
# CONTROL ENDPOINTS
# ============================================================================

@app.route('/api/mesh/abort', methods=['POST'])
def abort_installation():
    """Abort an installation"""
    data = request.json or {}
    installer_id = data.get("installer_id")
    reason = data.get("reason", "Aborted by Z.ai")
    
    msgs = load_json(MESSAGES_FILE, {"pending": []})
    msgs["pending"].append({
        "message_id": str(uuid.uuid4()),
        "message_type": "abort",
        "sender_id": "z_ai",
        "receiver_id": installer_id,
        "timestamp": time.time(),
        "payload": {"reason": reason}
    })
    save_json(MESSAGES_FILE, msgs)
    
    logger.warning(f"[ABORT] Sent to {installer_id[:8] if installer_id else 'unknown'}...: {reason}")
    
    return jsonify({
        "status": "queued",
        "reason": reason,
        "timestamp": time.time()
    })

@app.route('/api/mesh/pause', methods=['POST'])
def pause_installation():
    """Pause an installation"""
    data = request.json or {}
    installer_id = data.get("installer_id")
    
    if not installer_id:
        return jsonify({"error": "installer_id required"}), 400
    
    msgs = load_json(MESSAGES_FILE, {"pending": []})
    msgs["pending"].append({
        "message_id": str(uuid.uuid4()),
        "message_type": "pause",
        "sender_id": "z_ai",
        "receiver_id": installer_id,
        "timestamp": time.time(),
        "payload": {}
    })
    save_json(MESSAGES_FILE, msgs)
    
    return jsonify({"status": "queued", "timestamp": time.time()})

@app.route('/api/mesh/resume', methods=['POST'])
def resume_installation():
    """Resume a paused installation"""
    data = request.json or {}
    installer_id = data.get("installer_id")
    
    if not installer_id:
        return jsonify({"error": "installer_id required"}), 400
    
    msgs = load_json(MESSAGES_FILE, {"pending": []})
    msgs["pending"].append({
        "message_id": str(uuid.uuid4()),
        "message_type": "resume",
        "sender_id": "z_ai",
        "receiver_id": installer_id,
        "timestamp": time.time(),
        "payload": {}
    })
    save_json(MESSAGES_FILE, msgs)
    
    return jsonify({"status": "queued", "timestamp": time.time()})

# ============================================================================
# KNOWLEDGE ENDPOINTS
# ============================================================================

@app.route('/api/mesh/knowledge', methods=['POST'])
def upload_knowledge():
    """Upload knowledge from Z.ai to share with KIInstallers"""
    data = request.json or {}
    knowledge_id = str(uuid.uuid4())
    
    logger.info(f"[KNOWLEDGE] Uploaded: {data.get('title', 'Unknown')}")
    
    return jsonify({
        "knowledge_id": knowledge_id,
        "status": "accepted",
        "timestamp": time.time()
    })

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    state = load_json(STATE_FILE, {})
    return jsonify({
        "status": "healthy",
        "version": "6.3.0-SCADA",
        "layers": {
            "control": "active",
            "chat": "active",
            "shadow": "active",
            "tunnel": "active"
        },
        "nodes": len(state.get("nodes", {})),
        "timestamp": time.time()
    })

# ============================================================================
# MAIN
# ============================================================================

def print_banner(port: int):
    """Print startup banner"""
    print("=" * 70)
    print("         MASTER KISWARM API - SCADA Architecture v6.3.0")
    print("=" * 70)
    print(f"  Port: {port}")
    print(f"  Host: 0.0.0.0")
    print()
    print("  LAYER 1 - SCADA CONTROL:")
    print("    GET  /api/mesh/status           - Mesh status")
    print("    GET  /api/mesh/messages         - Poll messages")
    print("    POST /api/mesh/register         - Register installer")
    print("    POST /api/mesh/status/<id>      - Report status")
    print("    POST /api/mesh/error/<id>       - Report error")
    print("    POST /api/mesh/fix              - Send fix")
    print()
    print("  LAYER 2 - A2A CHAT:")
    print("    POST /api/mesh/chat/send        - Send A2A message")
    print("    GET  /api/mesh/chat/poll        - Poll A2A messages")
    print()
    print("  LAYER 3 - SHADOW (Digital Twin):")
    print("    POST /api/mesh/shadow/update    - Update environment mirror")
    print("    GET  /api/mesh/shadow/get/<id>  - Get shadow state")
    print()
    print("  LAYER 4 - DIRECT TUNNELING:")
    print("    POST /api/mesh/tunnel/register  - Register bypass tunnel")
    print("    GET  /api/mesh/tunnel/get/<id>  - Get tunnel info")
    print("=" * 70)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Master KISWARM API Server v6.3.0')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='API port')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST, help='Host')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    # Initialize storage
    initialize_storage()
    
    # Print banner
    print_banner(args.port)
    
    # Start server
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )
