#!/usr/bin/env python3
"""
KISWARM6.0 - Master KISWARM API Server
======================================
Flask-based REST API for KI-to-KI Mesh Communication

This server provides:
1. Registration endpoint for KIInstaller instances
2. Status reporting and monitoring
3. Error reporting and fix delivery
4. Message queuing between Z.ai and KIInstaller

Setup:
    pip install flask flask-cors
    python master_kiswarm_api.py --port 5002

Architecture:
    KIInstaller (Colab) <--> ngrok tunnel <--> Master API <--> Z.ai (GLM5)

Author: KISWARM Development Team
Version: 6.2.0
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
    """Initialize storage files"""
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
    
    if not os.path.exists(MESSAGES_FILE):
        initial_messages = {
            "pending": [],
            "processed": [],
            "created_at": time.time()
        }
        save_json(MESSAGES_FILE, initial_messages)
        logger.info("Initialized messages file")

# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ============================================================================
# MESH STATUS ENDPOINTS
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
    """
    Get full mesh state including all registered nodes.
    
    Returns:
        {
            "mesh_status": "online",
            "nodes": {...},
            "statistics": {...}
        }
    """
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
# MESSAGE ENDPOINTS
# ============================================================================

@app.route('/api/mesh/messages', methods=['GET'])
def get_messages():
    """
    Get pending messages from KIInstallers.
    
    This is what Z.ai polls to see what's happening.
    
    Query Parameters:
        limit: Max messages to return (default: 50)
    
    Returns:
        {
            "count": 5,
            "messages": [...],
            "timestamp": 1234567890.123
        }
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
# REGISTRATION ENDPOINTS
# ============================================================================

@app.route('/api/mesh/register', methods=['POST'])
def register():
    """
    Register a new KIInstaller instance.
    
    Request Body:
        {
            "installer_name": "colab-fieldtest-002",
            "environment": "colab",
            "capabilities": ["install", "deploy", "report"]
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
            "message_timeout": 60
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
# STATUS REPORTING ENDPOINTS
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
# ERROR REPORTING ENDPOINTS
# ============================================================================

@app.route('/api/mesh/error/<installer_id>', methods=['POST'])
def report_error(installer_id: str):
    """
    Report error from KIInstaller.
    
    This triggers Z.ai notification for potential intervention.
    
    Request Body:
        {
            "error_type": "ImportError",
            "error_message": "No module named 'flask_cors'",
            "module": "M58",
            "context": {...}
        }
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
# FIX DELIVERY ENDPOINTS
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
# CONTROL ENDPOINTS
# ============================================================================

@app.route('/api/mesh/abort', methods=['POST'])
def abort_installation():
    """
    Abort an installation.
    
    Request Body:
        {
            "installer_id": "target-installer-id",
            "reason": "Critical failure detected"
        }
    """
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
    """
    Upload knowledge from Z.ai to share with KIInstallers.
    
    Request Body:
        {
            "knowledge_type": "pattern",
            "title": "Fix for flask_cors import error",
            "problem_signature": "ImportError:flask_cors",
            "solution": {...},
            "environments": ["colab", "local"]
        }
    """
    data = request.json or {}
    
    # Store knowledge (in production, this would go to a knowledge base)
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
    return jsonify({"status": "healthy", "timestamp": time.time()})

# ============================================================================
# MAIN
# ============================================================================

def print_banner(port: int):
    """Print startup banner"""
    print("=" * 60)
    print("MASTER KISWARM API")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"Host: 0.0.0.0")
    print()
    print("Endpoints:")
    print("  GET  /api/mesh/status           - Mesh status")
    print("  GET  /api/mesh/messages         - Poll messages")
    print("  POST /api/mesh/register         - Register installer")
    print("  POST /api/mesh/status/<id>      - Report status")
    print("  POST /api/mesh/error/<id>       - Report error")
    print("  POST /api/mesh/fix              - Send fix")
    print("  POST /api/mesh/abort            - Abort installation")
    print("=" * 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Master KISWARM API Server')
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
