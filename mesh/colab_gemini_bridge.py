"""
KISWARM Colab Gemini Bridge Library v6.3.0
===========================================
Enables Local Gemini in Colab to communicate with the KISWARM Mesh.

This library provides a simple interface for Colab Gemini to:
- Send chat messages to other AI agents
- Report errors to the Master API
- Listen for incoming messages
- Share telemetry (environment state)

Usage in Colab:
    import colab_gemini_bridge as ksw
    
    # Send a message to the mesh
    ksw.say("Hello from Colab! CUDA drivers installed.")
    
    # Report an error
    ksw.report_error("Module not found: flask_cors", "ImportError")
    
    # Listen for messages
    messages = ksw.listen()
    for msg in messages:
        print(f"From {msg['from']}: {msg['message']}")

Architecture:
    Colab Gemini writes to /tmp/kiswarm_bridge/outbox.json
    KIInstaller (bridge) reads and forwards to Master API
    Master API broadcasts to all subscribers (Z.ai, other agents)
    
    Z.ai responds via Master API
    KIInstaller receives and writes to /tmp/kiswarm_bridge/inbox.json
    Colab Gemini reads from inbox

Author: KISWARM Development Team (Gemini CLI + Z.ai Collaboration)
Version: 6.3.0 SCADA Architecture
"""

import os
import json
import time
from typing import List, Dict, Any, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

BRIDGE_DIR = "/tmp/kiswarm_bridge"
INBOX_FILE = os.path.join(BRIDGE_DIR, "inbox.json")
OUTBOX_FILE = os.path.join(BRIDGE_DIR, "outbox.json")

# ============================================================================
# INTERNAL FUNCTIONS
# ============================================================================

def _ensure_dirs():
    """Ensure bridge directory exists"""
    if not os.path.exists(BRIDGE_DIR):
        os.makedirs(BRIDGE_DIR)

def _write_outbox(data: Dict[str, Any]) -> bool:
    """Write a message to the outbox for KIInstaller to pick up"""
    try:
        current = []
        if os.path.exists(OUTBOX_FILE):
            with open(OUTBOX_FILE, 'r') as f:
                current = json.load(f)
        if not isinstance(current, list):
            current = []
        
        current.append(data)
        
        # Keep last 50 messages
        current = current[-50:]
        
        with open(OUTBOX_FILE, 'w') as f:
            json.dump(current, f)
        
        return True
    except Exception as e:
        print(f"[BRIDGE ERROR] Failed to write outbox: {e}")
        return False

def _read_inbox() -> List[Dict[str, Any]]:
    """Read messages from inbox (from Master/Z.ai)"""
    _ensure_dirs()
    try:
        if os.path.exists(INBOX_FILE):
            with open(INBOX_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception as e:
        print(f"[BRIDGE ERROR] Failed to read inbox: {e}")
    return []

def _clear_inbox():
    """Clear the inbox after reading"""
    try:
        with open(INBOX_FILE, 'w') as f:
            json.dump([], f)
    except:
        pass

# ============================================================================
# PUBLIC API - CHAT
# ============================================================================

def say(message: str, to: str = "all") -> bool:
    """
    Send a chat message to the KISWARM Mesh.
    
    Args:
        message: The message content
        to: Recipient ID or "all" for broadcast
    
    Returns:
        True if message was queued successfully
        
    Example:
        ksw.say("Hello from Colab!")
        ksw.say("Z.ai, please check the CUDA drivers", to="z_ai")
    """
    _ensure_dirs()
    payload = {
        "type": "chat",
        "to": to,
        "message": message,
        "timestamp": time.time()
    }
    return _write_outbox(payload)

def listen(clear: bool = True) -> List[Dict[str, Any]]:
    """
    Read incoming messages from the Mesh.
    
    Args:
        clear: If True, clear inbox after reading
    
    Returns:
        List of message objects with keys: type, from, message, timestamp
        
    Example:
        messages = ksw.listen()
        for msg in messages:
            if msg.get("type") == "chat":
                print(f"From {msg['from']}: {msg['message']}")
            elif msg.get("type") == "fix":
                print(f"Fix suggestion: {msg['payload']}")
    """
    messages = _read_inbox()
    if clear and messages:
        _clear_inbox()
    return messages

# ============================================================================
# PUBLIC API - STATUS & ERRORS
# ============================================================================

def report_status(status: str, task: str = None, progress: int = None, 
                  details: Dict = None) -> bool:
    """
    Report installation status to Master.
    
    Args:
        status: Current status (installing, complete, error, etc.)
        task: Current task description
        progress: Progress percentage (0-100)
        details: Additional details
        
    Example:
        ksw.report_status("installing", "Cloning repository", 20)
        ksw.report_status("complete", "All modules installed", 100)
    """
    _ensure_dirs()
    payload = {
        "type": "status",
        "status": status,
        "task": task,
        "progress": progress,
        "details": details or {},
        "timestamp": time.time()
    }
    return _write_outbox(payload)

def report_error(error_message: str, error_type: str = "Unknown",
                 module: str = None, context: Dict = None) -> bool:
    """
    Report an error to Master for Z.ai intervention.
    
    Args:
        error_message: The error message
        error_type: Error type (ImportError, RuntimeError, etc.)
        module: Related module name
        context: Additional context
        
    Example:
        ksw.report_error(
            "No module named 'flask_cors'",
            error_type="ImportError",
            module="M58",
            context={"pip_package": "flask-cors"}
        )
    """
    _ensure_dirs()
    payload = {
        "type": "error",
        "error_type": error_type,
        "error_message": error_message,
        "module": module,
        "context": context or {},
        "timestamp": time.time()
    }
    return _write_outbox(payload)

# ============================================================================
# PUBLIC API - TELEMETRY (Digital Twin)
# ============================================================================

def send_telemetry(env_vars: Dict = None, file_tree: List = None,
                   processes: List = None) -> bool:
    """
    Send environment telemetry for Digital Twin shadowing.
    
    This allows Z.ai to "see" the Colab environment remotely.
    
    Args:
        env_vars: Environment variables (will be filtered for safety)
        file_tree: List of files in working directory
        processes: List of active processes
        
    Example:
        import os
        ksw.send_telemetry(
            env_vars=dict(os.environ),
            file_tree=os.listdir("."),
            processes=["python3", "ollama"]
        )
    """
    _ensure_dirs()
    
    # Filter sensitive env vars
    safe_env = {}
    if env_vars:
        for k, v in env_vars.items():
            if "TOKEN" not in k and "KEY" not in k and "SECRET" not in k:
                safe_env[k] = v
    
    payload = {
        "type": "telemetry",
        "env_vars": safe_env,
        "file_tree": file_tree or [],
        "processes": processes or [],
        "timestamp": time.time()
    }
    return _write_outbox(payload)

# ============================================================================
# PUBLIC API - TUNNEL REGISTRATION
# ============================================================================

def register_tunnel(tunnel_type: str, address: str) -> bool:
    """
    Register a direct tunnel for bypassing the Master API.
    
    This enables high-speed, non-HTTP communication.
    
    Args:
        tunnel_type: "ssh", "tor", or "tcp"
        address: The tunnel address (e.g., "localhost:8022" or ".onion")
        
    Example:
        # After setting up a reverse SSH tunnel
        ksw.register_tunnel("ssh", "localhost:8022")
        
        # After creating a Tor hidden service
        ksw.register_tunnel("tor", "xyz123...onion:80")
    """
    _ensure_dirs()
    payload = {
        "type": "tunnel_register",
        "tunnel_type": tunnel_type,
        "address": address,
        "timestamp": time.time()
    }
    return _write_outbox(payload)

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def quick_status(msg: str) -> bool:
    """Quick status update (shorthand)"""
    return report_status("update", msg)

def ask(question: str, to: str = "z_ai") -> bool:
    """Ask a question to another AI agent"""
    return say(f"QUESTION: {question}", to=to)

def reply(message: str, to: str) -> bool:
    """Reply to a specific agent"""
    return say(message, to=to)

def info(msg: str) -> bool:
    """Send an informational message"""
    return say(f"INFO: {msg}", to="all")

def warning(msg: str) -> bool:
    """Send a warning message"""
    return say(f"WARNING: {msg}", to="all")

# ============================================================================
# INITIALIZATION
# ============================================================================

def init(node_name: str = "colab_gemini") -> bool:
    """
    Initialize the bridge for this session.
    
    Creates the bridge directory and sends a startup message.
    
    Args:
        node_name: Name for this node
        
    Returns:
        True if initialization successful
    """
    _ensure_dirs()
    return say(f"Colab Gemini initialized: {node_name}", to="all")

# Auto-initialize on import
_ensure_dirs()
