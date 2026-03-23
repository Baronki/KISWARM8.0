#!/usr/bin/env python3
"""
KISWARM6.0 - Local KI-to-KI Mesh Bridge for Colab
==================================================
Enables direct communication between KIInstaller and Gemini CLI in Colab

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                         COLAB                                │
    │                                                              │
    │   ┌──────────────┐      ┌──────────────┐                    │
    │   │ KIInstaller  │◄────►│  Gemini CLI  │                    │
    │   │   (Python)   │      │    (AI)      │                    │
    │   │              │      │              │                    │
    │   │ - Install    │      │ - Local Fix  │                    │
    │   │ - Report     │      │ - Full Env   │                    │
    │   │ - Execute    │      │ - Instant    │                    │
    │   └──────────────┘      └──────────────┘                    │
    │          │                                                    │
    │          │ ngrok                                              │
    │          ▼                                                    │
    │   ┌──────────────────────────────────────────────────────┐   │
    │   │              Master KISWARM + Z.ai                   │   │
    │   │              (Remote Backup)                         │   │
    │   └──────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────┘

Author: KISWARM Development Team
Version: 6.2.1
License: See LICENSE file
"""

import json
import os
import time
import threading
import subprocess
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import queue

# ============================================================================
# CONFIGURATION
# ============================================================================

LOCAL_MESH_DIR = "/tmp/kiswarm_local_mesh"
LOCAL_MESSAGE_FILE = f"{LOCAL_MESH_DIR}/messages.json"
LOCAL_FIX_FILE = f"{LOCAL_MESH_DIR}/fixes.json"
LOCAL_STATE_FILE = f"{LOCAL_MESH_DIR}/state.json"
LOCAL_COMMAND_FILE = f"{LOCAL_MESH_DIR}/commands.json"

# ============================================================================
# LOCAL MESH MANAGER
# ============================================================================

class LocalMeshManager:
    """
    Manages local KI-to-KI communication in Colab.
    
    This enables KIInstaller to communicate with Gemini CLI directly,
    without network latency, with full environment access.
    """
    
    def __init__(self, mesh_id: str = "colab-local-mesh"):
        self.mesh_id = mesh_id
        self.mesh_dir = Path(LOCAL_MESH_DIR)
        self._ensure_mesh_dir()
        self._lock = threading.Lock()
        
    def _ensure_mesh_dir(self):
        """Ensure mesh directory exists"""
        self.mesh_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize files if not exist
        for file_path, default_content in [
            (LOCAL_MESSAGE_FILE, {"pending": [], "processed": []}),
            (LOCAL_FIX_FILE, {"pending": []}),
            (LOCAL_STATE_FILE, {"status": "initialized", "nodes": {}}),
            (LOCAL_COMMAND_FILE, {"pending": []})
        ]:
            if not os.path.exists(file_path):
                self._write_json(file_path, default_content)
    
    def _read_json(self, path: str) -> Dict:
        """Read JSON file safely"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _write_json(self, path: str, data: Dict):
        """Write JSON file safely"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    # ========================================================================
    # KIINSTALLER INTERFACE (Python Side)
    # ========================================================================
    
    def report_status(self, installer_id: str, status: str, task: str = None,
                      progress: int = None, details: Dict = None) -> str:
        """
        Report status to local mesh (visible by Gemini CLI).
        
        Args:
            installer_id: Installer instance ID
            status: Current status
            task: Current task
            progress: Progress percentage
            details: Additional details
            
        Returns:
            Message ID
        """
        message_id = self._generate_id()
        
        message = {
            "message_id": message_id,
            "message_type": "status_update",
            "sender_id": installer_id,
            "sender_type": "kiinstaller",
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "payload": {
                "status": status,
                "task": task,
                "progress": progress,
                "details": details or {}
            }
        }
        
        with self._lock:
            data = self._read_json(LOCAL_MESSAGE_FILE)
            data["pending"].append(message)
            self._write_json(LOCAL_MESSAGE_FILE, data)
        
        print(f"[LOCAL_MESH] Status: {status} - {task} ({progress or 0}%)")
        return message_id
    
    def report_error(self, installer_id: str, error_type: str, error_message: str,
                     module: str = None, context: Dict = None, stack_trace: str = None) -> str:
        """
        Report error to local mesh (Gemini CLI will see this immediately).
        
        Args:
            installer_id: Installer instance ID
            error_type: Error type (ImportError, RuntimeError, etc.)
            error_message: Error message
            module: Related module
            context: Additional context
            stack_trace: Full stack trace
            
        Returns:
            Message ID
        """
        message_id = self._generate_id()
        
        message = {
            "message_id": message_id,
            "message_type": "error_report",
            "priority": 0,  # Highest priority
            "sender_id": installer_id,
            "sender_type": "kiinstaller",
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "payload": {
                "error_type": error_type,
                "error_message": error_message,
                "module": module,
                "context": context or {},
                "stack_trace": stack_trace
            }
        }
        
        with self._lock:
            data = self._read_json(LOCAL_MESSAGE_FILE)
            data["pending"].append(message)
            self._write_json(LOCAL_MESSAGE_FILE, data)
        
        print(f"[LOCAL_MESH] ⚠️ ERROR: {error_type} - {error_message}")
        print(f"[LOCAL_MESH] Gemini CLI can now see and respond to this error!")
        return message_id
    
    def request_fix(self, installer_id: str, error_type: str, error_message: str,
                    module: str = None, context: Dict = None, timeout: float = 60.0) -> Optional[Dict]:
        """
        Request fix from Gemini CLI and wait for response.
        
        This is a BLOCKING call that waits for Gemini CLI to respond.
        
        Args:
            installer_id: Installer instance ID
            error_type: Error type
            error_message: Error message
            module: Related module
            context: Additional context
            timeout: Maximum wait time in seconds
            
        Returns:
            Fix suggestion or None if timeout
        """
        # Report error first
        self.report_error(installer_id, error_type, error_message, module, context)
        
        print(f"[LOCAL_MESH] Waiting for Gemini CLI fix (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for fix
            fixes = self._read_json(LOCAL_FIX_FILE)
            pending = fixes.get("pending", [])
            
            for fix in pending:
                if fix.get("target_id") == installer_id:
                    # Remove from pending
                    with self._lock:
                        fixes["pending"] = [f for f in pending if f.get("fix_id") != fix.get("fix_id")]
                        self._write_json(LOCAL_FIX_FILE, fixes)
                    
                    print(f"[LOCAL_MESH] ✅ Fix received from Gemini CLI!")
                    return fix
            
            time.sleep(0.5)
        
        print(f"[LOCAL_MESH] ⏱️ Timeout waiting for fix")
        return None
    
    def check_commands(self, installer_id: str) -> List[Dict]:
        """
        Check for commands from Gemini CLI.
        
        Args:
            installer_id: Installer instance ID
            
        Returns:
            List of commands
        """
        commands = self._read_json(LOCAL_COMMAND_FILE)
        pending = commands.get("pending", [])
        
        # Filter for this installer
        my_commands = [c for c in pending if c.get("target_id") == installer_id]
        
        if my_commands:
            # Remove from pending
            with self._lock:
                commands["pending"] = [c for c in pending if c.get("target_id") != installer_id]
                self._write_json(LOCAL_COMMAND_FILE, commands)
        
        return my_commands
    
    def report_fix_applied(self, installer_id: str, fix_id: str, success: bool, 
                           result: str = None):
        """Report that a fix was applied"""
        message = {
            "message_id": self._generate_id(),
            "message_type": "fix_applied",
            "sender_id": installer_id,
            "timestamp": time.time(),
            "payload": {
                "fix_id": fix_id,
                "success": success,
                "result": result
            }
        }
        
        with self._lock:
            data = self._read_json(LOCAL_MESSAGE_FILE)
            data["pending"].append(message)
            self._write_json(LOCAL_MESSAGE_FILE, data)
    
    # ========================================================================
    # GEMINI CLI INTERFACE (AI Side)
    # ========================================================================
    
    def get_pending_messages(self, limit: int = 50) -> List[Dict]:
        """
        Get pending messages for Gemini CLI to process.
        
        Returns:
            List of pending messages
        """
        data = self._read_json(LOCAL_MESSAGE_FILE)
        return data.get("pending", [])[:limit]
    
    def send_fix(self, fix_id: str, target_id: str, fix_type: str, 
                 title: str, description: str, solution: Dict,
                 confidence: float = 0.9) -> str:
        """
        Send fix suggestion from Gemini CLI to KIInstaller.
        
        Args:
            fix_id: Unique fix ID
            target_id: Target installer ID
            fix_type: Type of fix (pip_install, code_patch, config_change)
            title: Fix title
            description: Fix description
            solution: Solution details
            confidence: Confidence level (0-1)
            
        Returns:
            Fix ID
        """
        fix = {
            "fix_id": fix_id or self._generate_id(),
            "target_id": target_id,
            "fix_type": fix_type,
            "title": title,
            "description": description,
            "solution": solution,
            "confidence": confidence,
            "source": "gemini_cli",
            "timestamp": time.time()
        }
        
        with self._lock:
            data = self._read_json(LOCAL_FIX_FILE)
            data["pending"].append(fix)
            self._write_json(LOCAL_FIX_FILE, data)
        
        print(f"[LOCAL_MESH] Fix sent: {title}")
        return fix["fix_id"]
    
    def send_command(self, target_id: str, command: str, payload: Dict = None) -> str:
        """
        Send command from Gemini CLI to KIInstaller.
        
        Args:
            target_id: Target installer ID
            command: Command type (abort, pause, resume, execute)
            payload: Command payload
            
        Returns:
            Command ID
        """
        cmd = {
            "command_id": self._generate_id(),
            "target_id": target_id,
            "command": command,
            "payload": payload or {},
            "timestamp": time.time()
        }
        
        with self._lock:
            data = self._read_json(LOCAL_COMMAND_FILE)
            data["pending"].append(cmd)
            self._write_json(LOCAL_COMMAND_FILE, data)
        
        print(f"[LOCAL_MESH] Command sent: {command}")
        return cmd["command_id"]
    
    def get_state(self) -> Dict:
        """Get current mesh state"""
        return self._read_json(LOCAL_STATE_FILE)
    
    def update_state(self, updates: Dict):
        """Update mesh state"""
        with self._lock:
            state = self._read_json(LOCAL_STATE_FILE)
            state.update(updates)
            state["last_update"] = time.time()
            self._write_json(LOCAL_STATE_FILE, state)
    
    def clear_messages(self):
        """Clear processed messages"""
        with self._lock:
            data = self._read_json(LOCAL_MESSAGE_FILE)
            data["processed"].extend(data["pending"])
            data["pending"] = []
            self._write_json(LOCAL_MESSAGE_FILE, data)
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())


# ============================================================================
# KIINSTALLER LOCAL MESH CLIENT
# ============================================================================

class KIInstallerLocalMeshClient:
    """
    Client for KIInstaller to use local mesh communication.
    
    This provides a simple interface for KIInstaller to:
    - Report status to Gemini CLI
    - Report errors and request fixes
    - Check for commands from Gemini CLI
    
    Example:
        client = KIInstallerLocalMeshClient("installer-001")
        
        # Report progress
        client.report_status("installing", "Cloning repository", 20)
        
        # Report error and wait for fix
        fix = client.request_fix(
            error_type="ImportError",
            error_message="No module named 'flask_cors'",
            module="M58",
            timeout=60.0
        )
        
        if fix:
            client.apply_fix(fix)
    """
    
    def __init__(self, installer_id: str = None):
        self.installer_id = installer_id or self._generate_id()
        self.mesh = LocalMeshManager()
        self._registered = False
        
    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
    
    def register(self, name: str = "kiinstaller", capabilities: List[str] = None) -> bool:
        """Register with local mesh"""
        state = self.mesh.get_state()
        state["nodes"][self.installer_id] = {
            "node_id": self.installer_id,
            "node_name": name,
            "node_type": "kiinstaller",
            "capabilities": capabilities or ["install", "deploy", "report"],
            "status": "online",
            "registered_at": time.time()
        }
        self.mesh.update_state(state)
        self._registered = True
        print(f"[LOCAL_MESH] Registered: {self.installer_id}")
        return True
    
    def report_status(self, status: str, task: str = None, 
                      progress: int = None, details: Dict = None):
        """Report status to local mesh"""
        return self.mesh.report_status(
            self.installer_id, status, task, progress, details
        )
    
    def report_error(self, error_type: str, error_message: str,
                     module: str = None, context: Dict = None):
        """Report error to local mesh"""
        return self.mesh.report_error(
            self.installer_id, error_type, error_message, module, context
        )
    
    def request_fix(self, error_type: str, error_message: str,
                    module: str = None, context: Dict = None,
                    timeout: float = 60.0) -> Optional[Dict]:
        """Request fix and wait for response"""
        return self.mesh.request_fix(
            self.installer_id, error_type, error_message, module, context, timeout
        )
    
    def check_commands(self) -> List[Dict]:
        """Check for commands from Gemini CLI"""
        return self.mesh.check_commands(self.installer_id)
    
    def apply_fix(self, fix: Dict) -> bool:
        """Apply a fix suggestion"""
        solution = fix.get("solution", {})
        commands = solution.get("commands", [])
        
        print(f"[LOCAL_MESH] Applying fix: {fix.get('title')}")
        
        for cmd in commands:
            print(f"[LOCAL_MESH] Executing: {cmd}")
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode != 0:
                    print(f"[LOCAL_MESH] Command failed: {result.stderr}")
                    return False
            except Exception as e:
                print(f"[LOCAL_MESH] Execution error: {e}")
                return False
        
        # Report success
        self.mesh.report_fix_applied(
            self.installer_id, 
            fix.get("fix_id"), 
            True, 
            "Fix applied successfully"
        )
        
        return True
    
    def send_heartbeat(self):
        """Send heartbeat to update last_seen"""
        state = self.mesh.get_state()
        if self.installer_id in state.get("nodes", {}):
            state["nodes"][self.installer_id]["last_seen"] = time.time()
            self.mesh.update_state(state)


# ============================================================================
# GEMINI CLI MESH INTERFACE
# ============================================================================

class GeminiCLIMeshInterface:
    """
    Interface for Gemini CLI to interact with local mesh.
    
    This provides functions for Gemini CLI to:
    - Read messages from KIInstaller
    - Send fix suggestions
    - Send commands
    - Monitor installation progress
    
    Example for Gemini CLI:
        interface = GeminiCLIMeshInterface()
        
        # Check for messages
        messages = interface.get_messages()
        
        for msg in messages:
            if msg["message_type"] == "error_report":
                # Send fix
                interface.send_fix(
                    target_id=msg["sender_id"],
                    fix_type="pip_install",
                    title="Install missing module",
                    solution={"commands": ["pip install flask-cors"]}
                )
    """
    
    def __init__(self):
        self.mesh = LocalMeshManager()
    
    def get_messages(self, limit: int = 50) -> List[Dict]:
        """Get pending messages from KIInstaller"""
        return self.mesh.get_pending_messages(limit)
    
    def get_latest_error(self) -> Optional[Dict]:
        """Get the most recent error message"""
        messages = self.mesh.get_pending_messages()
        errors = [m for m in messages if m.get("message_type") == "error_report"]
        return errors[-1] if errors else None
    
    def send_fix(self, target_id: str, fix_type: str, title: str,
                 description: str = None, solution: Dict = None,
                 confidence: float = 0.9) -> str:
        """Send fix suggestion to KIInstaller"""
        return self.mesh.send_fix(
            fix_id=None,
            target_id=target_id,
            fix_type=fix_type,
            title=title,
            description=description or "",
            solution=solution or {},
            confidence=confidence
        )
    
    def send_abort(self, target_id: str, reason: str = "Aborted by Gemini CLI"):
        """Send abort command to KIInstaller"""
        return self.mesh.send_command(target_id, "abort", {"reason": reason})
    
    def send_pause(self, target_id: str):
        """Send pause command to KIInstaller"""
        return self.mesh.send_command(target_id, "pause")
    
    def send_resume(self, target_id: str):
        """Send resume command to KIInstaller"""
        return self.mesh.send_command(target_id, "resume")
    
    def get_state(self) -> Dict:
        """Get current mesh state"""
        return self.mesh.get_state()
    
    def clear_processed(self):
        """Clear processed messages"""
        self.mesh.clear_messages()


# ============================================================================
# GEMINI CLI PROMPT GENERATOR
# ============================================================================

def generate_gemini_cli_prompt() -> str:
    """
    Generate a prompt for Gemini CLI explaining how to use the local mesh.
    
    This can be used to instruct Gemini CLI on how to interact with KIInstaller.
    """
    return """
# KISWARM Local Mesh Communication - Gemini CLI Instructions

You have access to a local mesh communication system that enables direct
interaction with KIInstaller (the installation agent running in this Colab).

## Quick Reference

```python
from local_mesh_bridge import GeminiCLIMeshInterface

# Initialize interface
mesh = GeminiCLIMeshInterface()

# Check for messages from KIInstaller
messages = mesh.get_messages()

# Get latest error
error = mesh.get_latest_error()

# Send fix to KIInstaller
mesh.send_fix(
    target_id="installer-id",
    fix_type="pip_install",
    title="Install missing module",
    solution={"commands": ["pip install flask-cors"]}
)

# Send commands
mesh.send_abort("installer-id", "Critical error detected")
mesh.send_pause("installer-id")
mesh.send_resume("installer-id")
```

## Message Types

- `status_update`: Installation progress reports
- `error_report`: Errors requiring your intervention
- `fix_applied`: Confirmation that a fix was applied

## Fix Types

- `pip_install`: Install Python package
- `code_patch`: Modify code
- `config_change`: Change configuration
- `command`: Execute shell command

## Your Role

1. Monitor messages from KIInstaller
2. Analyze errors and determine solutions
3. Send fix suggestions back
4. Monitor fix application results
5. Escalate to remote Z.ai if unable to resolve locally
"""


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Demonstrate local mesh communication"""
    print("=" * 60)
    print("KISWARM Local Mesh Communication Demo")
    print("=" * 60)
    
    # KIInstaller side
    installer = KIInstallerLocalMeshClient()
    installer.register("demo-installer")
    
    # Simulate installation progress
    installer.report_status("installing", "Starting installation", 5)
    installer.report_status("installing", "Cloning repository", 20)
    installer.report_status("installing", "Installing dependencies", 40)
    
    # Simulate error
    installer.report_error(
        error_type="ImportError",
        error_message="No module named 'flask_cors'",
        module="M58",
        context={"pip_package": "flask-cors"}
    )
    
    # Gemini CLI side
    gemini = GeminiCLIMeshInterface()
    
    # Check for messages
    messages = gemini.get_messages()
    print(f"\n[Gemini CLI] Received {len(messages)} messages")
    
    # Get latest error
    error = gemini.get_latest_error()
    if error:
        print(f"[Gemini CLI] Latest error: {error['payload']['error_type']}")
        
        # Send fix
        fix_id = gemini.send_fix(
            target_id=error["sender_id"],
            fix_type="pip_install",
            title="Install flask-cors",
            description="The flask_cors module is required for CORS support",
            solution={"commands": ["pip install flask-cors"]},
            confidence=0.98
        )
        print(f"[Gemini CLI] Fix sent: {fix_id}")
    
    # KIInstaller checks for fix
    commands = installer.check_commands()
    print(f"\n[KIInstaller] Received {len(commands)} commands")
    
    # Check for fixes (would normally be polled)
    mesh = LocalMeshManager()
    fixes = mesh._read_json(LOCAL_FIX_FILE)
    print(f"[KIInstaller] Pending fixes: {len(fixes.get('pending', []))}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
